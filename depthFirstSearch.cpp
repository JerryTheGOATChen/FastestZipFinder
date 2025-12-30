#include <iostream>
#include <vector>
#include <stack>

using namespace std;
//Using industry standard cause using pointers would just take too long for now...
//Using undirected cause it makes more sense in DFS

class Graph
{
	private:
		int elements;
		vector<vector<int>> adj;
		vector<bool> visited;
		vector<int> order;
		
	public:
		Graph(int elements);
		void addEdge(int x, int y);
		void recursivePreOrder(int x);
		void recursivePostOrder(int x);
		void iterativePreOrder(int x);
		bool hamiltonDFS(int x);
};

Graph::Graph(int elements)
{
	this -> elements = elements;
	adj.resize(elements);
	visited.resize(elements, false);
	order.resize(elements);
}

void Graph::addEdge(int x, int y)
{
	adj[x].push_back(y);
	adj[y].push_back(x);
}

void Graph::recursivePreOrder(int x)
{
	visited[x] = true;
	order.push_back(x);
	for(int i = 0; i < adj[x].size(); i++)
	{
		int y = adj[x][i];
		if(!visited[y])
		{
			recursivePreOrder(y);
		}
	}
}

void Graph::recursivePostOrder(int x)
{
	visited[x] = true;
	for (int i = 0; i < adj[x].size(); i++)
	{
		int y = adj[x][i];
		if(!visited[y])
		{
			recursivePostOrder(x);
		}
	}
	order.push_back(x);
}

void Graph::iterativePreOrder(int x)
{
	visited[x] = true;
	stack<int> st;
	
	st.push(x);
	
}

bool Graph::hamiltonDFS(int x)
{
	
}

int main()
{
	return 0;
}