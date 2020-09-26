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
esac
