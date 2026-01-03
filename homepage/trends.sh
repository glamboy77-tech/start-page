#!/bin/bash
export PYTHONIOENCODING=utf-8

# 현재 디렉토리(homepage 폴더)로 이동
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 가상환경 파이썬 위치 직접 지정
VENV_PYTHON="/home/glamboy/mybots/venv/bin/python3"

# 트렌드 엔진 실행
$VENV_PYTHON trends_engine.py