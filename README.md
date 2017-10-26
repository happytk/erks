
[![Build Status](https://travis-ci.com/happytk/ercc.svg?token=CjbpzCcx5vFmGVpZPFkf&branch=master)](https://travis-ci.com/happytk/ercc)
[![Coverage Status](https://coveralls.io/repos/github/happytk/ercc/badge.svg?t=lojNVE)](https://coveralls.io/github/happytk/ercc)

# ercc-coding-convention

## frontend

- bootstrap-table 사용하기
- parsleyjs로 validation하기. 일반적으로 wtform의 field에서 validator를 선언하면 자동으로 연결됩니다.

## backend

- 항상 wtform으로 post-data 검증하기
- model의 objects queryset은 건드리지 않습니다. 항상 전체를 return하는 것으로 약속
- head_objects는 의미있는 전체를 return하는 것으로 약속 (변경관리되고 있다면 최상, 삭제된 것이 있다면 제외하고)
