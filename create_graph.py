import pickle

from igraph import *

(book, edges, queue, processed, my_id) = pickle.load(open("state.pkl", "rb"))

g = Graph()
g.add_vertex('')
degree = {}


def update_degree(id):
    if id in degree:
        degree[id] += 1
    else:
        degree[id] = 1


ego_nodes = [my_id]
for id1, id2 in edges:
    if id1 == my_id and id2 not in ego_nodes:
        ego_nodes.append(id2)

    if id2 == my_id and id1 not in ego_nodes:
        ego_nodes.append(id1)


def filter_id(id):
    return id not in book or id not in ego_nodes


deleted = 0
for id1, id2 in edges:
    if filter_id(id1) or filter_id(id2):
        deleted += 1
        continue
    if book[id1] not in g.vs['name']:
        g.add_vertex(book[id1])
    if book[id2] not in g.vs['name']:
        g.add_vertex(book[id2])
    g.add_edge(book[id1], book[id2])
print('Deleted', deleted, 'edges')
print(g.summary())
# pickle.dump(g, open("facebook.pkl", "wb"))
g.to_undirected()


walktrap = g.community_walktrap(steps=10)
walktrap_communities = walktrap.as_clustering(n=10)
g.vs.set_attribute_values('walktrap_communities', walktrap_communities.membership)

edge_betweenness_communities = g.community_edge_betweenness(directed=False).as_clustering(n=10)
g.vs.set_attribute_values('edge_betweenness_communities', edge_betweenness_communities.membership)

leading_eigenvector_communities = g.community_leading_eigenvector()
g.vs.set_attribute_values('leading_eigenvector_communities', leading_eigenvector_communities.membership)

label_propagation_communities = g.community_label_propagation()
g.vs.set_attribute_values('label_propagation_communities', label_propagation_communities.membership)

infomap_communities = g.community_infomap()
g.vs.set_attribute_values('infomap_communities', infomap_communities.membership)

# spinglass_communities = g.community_spinglass()
# g.vs.set_attribute_values('spinglass_communities', spinglass_communities.membership)


g.write_graphml('ego_network.graphml')
