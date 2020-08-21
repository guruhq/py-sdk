#!/bin/bash

case "$1" in
test)
  coverage run -m unittest && coverage report && coverage html
  if [ "$2" = "-v" ]; then
    open htmlcov/index.html
  fi
  ;;
docs)
  pydoc -p 9000 guru
  ;;
esac
