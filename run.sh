#!/bin/bash

case "$1" in
test)
  coverage run -m unittest && coverage report && coverage html
  ;;
docs)
  pydoc -p 9000 guru
  ;;
esac
