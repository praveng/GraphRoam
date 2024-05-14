# GraphRoam

<p align="center">
<img src="logo-graphroam.png" width="200">
</p>


**GraphRoam** is a Python library designed to efficiently generate random walks on large graphs using consumer-grade, RAM-limited hardware. By leveraging DuckDB and sparse matrix representations, GraphRoam ensures minimal memory usage while maintaining high performance.

## Features

- **RAM Efficiency**: Only the adjacency matrix is held in memory.
- **Flexible Vertex Naming**: Supports string or non-enumerated integer vertex names.
- **Directed Graphs**: Designed for directed, non-weighted graphs.
- **Disk-Based Random Walks**: Random walks are written to disk, not stored in memory.

## Installation

To install GraphRoam, you can use pip:

```sh
pip install graphroam
```

## Usage

To use GraphRoam, simply call the `graphroam` function with your parameters:

```python
from graphroam import graphroam

graphroam(
    source_target_parquet='path/to/your/graph.parquet',
    walks_per_node=10,
    max_steps_per_node=50,
    mem_limit=16,  # Memory limit in GB
    workers=-1     # Number of parallel workers (-1 to use all available cores)
)
```

### Parameters

- `source_target_parquet`: Path to your Parquet file containing the graph edges.
- `walks_per_node`: Number of random walks per node. Default is 10.
- `max_steps_per_node`: Maximum steps per node in each random walk. Default is 50.
- `mem_limit`: Memory limit in GB for DuckDB. Setting this too low could result in high disk usage and longer processing times. Default is 16.
- `workers`: Number of parallel workers. Default is -1 (uses all available cores).

## Input Requirements

- The graph should be a directed, non-weighted graph.
- If you have an undirected graph, you can duplicate your data and flip the edges before feeding it into GraphRoam.
- The input file should be a Parquet file with the first column as the source node and the second column as the target node. Column headers are not important.

## Output

- Random walks are saved as multiple CSV files in a folder called `random_walks`.

## How it Works

1. **Vertex Mapping**: GraphRoam uses DuckDB to efficiently map vertex names to integers.
2. **Sparse Matrix**: A sparse matrix representation of the adjacency matrix is constructed and held in memory.
3. **Random Walks**: The library generates random walks and writes them to disk, ensuring minimal memory usage.

```plaintext
.
├── graphroam/
│   ├── __init__.py
│   ├── graphroam.py
├── tests/
├── requirements.txt
├── README.md
└── random_walks/
    ├── walk_1.csv
    ├── walk_2.csv
    └── ...
```

## Example

```python
from graphroam import graphroam

# Perform random walks on a sample graph
graphroam(
    source_target_parquet='sample_graph.parquet',
    walks_per_node=20,
    max_steps_per_node=100,
    mem_limit=8,
    workers=4
)
```


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contribution

Feel free to open issues or pull requests if you have suggestions or features to add. Join us in making GraphRoam even better!
