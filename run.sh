#!/bin/bash

case "$1" in
test)
  coverage run -m unittest && coverage report && coverage html
  if [ "$2" = "-v" ]; then
    open htmlcov/index.html
  fi
  ;;
all)
  E2E=true coverage run -m unittest && coverage report && coverage html
  if [ "$2" = "-v" ]; then
    open htmlcov/index.html
  fi
  ;;
e2e)
  E2E=true coverage run -m unittest tests.test_e2e && coverage report && coverage html
  if [ "$2" = "-v" ]; then
    open htmlcov/index.html
  fi
  ;;
docs)
  pydoc -p 9000 guru
  ;;
*)
  echo ""
  echo "usage: sh run.sh <command> [-v]"
  echo ""
  echo "where <command> is one of the following:"
  echo ""
  echo "  test -- to run only unit tests"
  echo "  e2e -- to run only end-to-end tests"
  echo "  all -- to run unit and end-to-end tests"
  echo "  docs -- to generate documentation"
  echo ""
  echo "When running tests, use -v to open the coverage report in your browser."
  echo ""
  ;;
esac
