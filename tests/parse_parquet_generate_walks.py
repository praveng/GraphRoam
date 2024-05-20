import duckdb
import os
import pytest
import glob
from graphroam import graphroam


def parquet_generation(test_file):
    conn = duckdb.connect()
    conn.execute(""" CREATE TABLE test AS SELECT 'source' || CAST(FLOOR(10000 * random()) AS VARCHAR) AS source_node,
                    'target' || CAST(FLOOR(10000 * random()) AS VARCHAR) AS target_node FROM range(100000) """)
    conn.execute(""" COPY test TO 'test.parquet' (FORMAT 'parquet') """)
    conn.close()
    assert os.path.exists(test_file)


def test_graphroam():
    test_file = 'test.parquet'
    parquet_generation(test_file)
    graphroam(
        source_target_parquet=test_file,
        walks_per_node=10,
        max_steps_per_node=50,
        mem_limit=8,  # Memory limit in GB
        workers=2
    )
    os.remove(test_file)
    assert len(glob.glob('random_walks/random_walks_*.csv')) > 0
    files = glob.glob('random_walks/random_walks_*.csv')
    for file in files:
        os.remove(file)
    os.rmdir('random_walks')