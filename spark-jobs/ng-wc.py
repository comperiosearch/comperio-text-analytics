import sys
from argparse import ArgumentParser

from pyspark import SparkContext

# Basic sample Spark job for testing
# To run pass the 20 Newsgroups JSON formatted corpus file as the -f argument, set
# the SPARK_HOME environment variable and run with spark-submit or pyspark.as

# To run and edit within PyCharm add SPARK_HOME/python and SPARK_HOME/python/lib/py4j-x.x.x.x-src.zip
# to the interpreter paths in addition to setting SPARK_HOME in the run configuration.

def main():
    parser = ArgumentParser()
    parser.add_argument('-f', '--filename')
    opts = parser.parse_args()

    fn = opts.filename

    if not fn:
        sys.exit(1)

    sc = SparkContext(appName='ng-wc')

    rdd = sc.textFile(fn)

    n = rdd.count()

    print 'The 20 Newsgroups corpus has %d articles.' % n


if __name__ == '__main__':
    main()