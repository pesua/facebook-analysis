import re
import pickle
import os.path
import time
import datetime
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, InvalidSelectorException

#Add your credentials here
my_id = ''
my_email = ''
my_pwd = ''

driver = webdriver.Firefox()


def extract_friend(element):
    href = element.get_attribute('href')
    name = element.text

    if not href:
        return '', ''
    if "profile.php" in href:
        id = re.search('(\d+)', href, re.IGNORECASE).group(1)
    else:
        id = re.search('com\/(.*)\?', href, re.IGNORECASE).group(1)

    # print(name, href)
    return id, name


def read_friends():
    elems = driver.find_elements_by_css_selector('#objects_container table a')
    result = []
    for elem in elems:
        test1 = elem.text not in ['Message', 'More', 'Add Friend']
        test3 = "Mutual" not in elem.text
        test = test1 and test3

        if test:
            result.append(extract_friend(elem))
    return result


def get_friends(id, mutual=False):
    pattern = re.compile("\d+")
    if pattern.match(id):
        driver.get("https://m.facebook.com/profile.php?v=friends&id=" + id + ("&mutual=1" if mutual else ""))
    else:
        driver.get("https://m.facebook.com/" + id + "/friends" + ("?mutual=1" if mutual else ""))

    friends = []
    page = 0
    while True:
        page = page + 1
        newFriends = read_friends()
        if len(newFriends) < 36:
            newFriends = read_friends()  # some heisenbug here
        friends = friends + newFriends
        more_friends = driver.find_elements_by_css_selector('#m_more_friends a')
        if len(more_friends):
            more_friends[0].click()
            driver.implicitly_wait(5)

            def wait_for(condition_function):
                start_time = time.time()
                while time.time() < start_time + 10000:
                    if condition_function():
                        return True
                    else:
                        time.sleep(0.1)

            def link_has_gone_stale():
                try:
                    # poll the link with an arbitrary call
                    more_friends[0].find_elements_by_id('doesnt-matter')
                    return False
                except StaleElementReferenceException:
                    return True
                except InvalidSelectorException:
                    return True

            wait_for(link_has_gone_stale)
        else:
            break
    return friends


driver.get("https://m.facebook.com/")
driver.execute_script("document.getElementById('m_login_email').value = '%s'; " % my_email)
driver.execute_script("document.getElementsByName('pass')[0].value = '%s';" % my_pwd)
email_field = driver.find_element_by_name('login').click()

if os.path.isfile('state.pkl'):
    print('resuming processing')
    (book, edges, queue, processed) = pickle.load(open("state.pkl", "rb"))
    print('book:', len(book))
    print('edges:', len(edges))
    print('queue:', len(queue))
    print('processed:', len(processed))
else:
    book = {}
    friends = get_friends(my_id)
    queue = [id for (id, name) in friends]
    processed = [my_id]
    edges = [(my_id, friend_id) for (friend_id, friend_name) in friends]
    pickle.dump((book, edges, queue, processed), open("state.pkl", "wb"))

output_pattern = "{0:>27s}, {1:>20s}, {2:>4d}, {3:>4d}, {4:>4d}, {5:>4d}"
print(output_pattern.replace("d", "s")
    .format(
    "timestamp",
    "id",
    "book",
    "edges",
    "queue",
    "processed"
))
while len(queue) > 0:
    id = queue.pop()
    friends = get_friends(id, mutual=True)
    book.update(dict(friends))
    edges = edges + [(id, friend_id) for (friend_id, friend_name) in friends if friend_id not in processed]
    processed = processed + [id]
    pickle.dump((book, edges, queue, processed), open("state.pkl", "wb"))

    print(output_pattern.format(
        str(datetime.datetime.now()),
        id,
        len(book),
        len(edges),
        len(queue),
        len(processed)
    ))

driver.close()
