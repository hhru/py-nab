#!/bin/bash
set -e
#set -x

if [ -z "$1" ]
  then
    echo "Project argument is required (almatest/ararat)"
    exit 1
fi

if [ -z "$2" ]
  then
    echo "Bump argument is required (major/minor/...)"
    exit 1
fi

cd $1

get_version () {
  local version="$(poetry version | cut -d ' ' -f2)"
  echo "$version"
}

version="$(get_version)"
echo "Current version: $version"

poetry version $2
version="$(get_version)"

git add pyproject.toml
git commit -m "$1 release $version"
tag="$1-$version"
git tag -f $tag
git push origin -f $tag

echo "**************** FINISHED ****************"
echo "Do not forget to merge code into master!"
