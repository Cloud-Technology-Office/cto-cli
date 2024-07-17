# CHANGELOG



## v0.4.1 (2024-07-17)

### Fix

* fix: don&#39;t fail on the first invalid yaml
* fix: add missing `debug` and pass `--config-var` on strategy build ([`2a3bc60`](https://github.com/Cloud-Technology-Office/cto-cli/commit/2a3bc609c50f8b57b31af72495f10350bc532eda))

### Unknown

* Merge pull request #13 from Cloud-Technology-Office/debug ([`94d12d7`](https://github.com/Cloud-Technology-Office/cto-cli/commit/94d12d7d27730c778fa7be6c6359373dff3f8772))


## v0.4.0 (2024-07-03)

### Feature

* feat: Add support for multi repos
* feat: add support for deleting and modifing users
* feat: add regenerating tokens for users
* feat: support read/read_write auth for paths ([`9b3c491`](https://github.com/Cloud-Technology-Office/cto-cli/commit/9b3c491386f16cd3eca4194c121a48ff76560fb3))

### Unknown

* Merge pull request #12 from Cloud-Technology-Office/muli_repos

Multi repos support ([`9be1d94`](https://github.com/Cloud-Technology-Office/cto-cli/commit/9be1d94fb0ea3be66d1426eaa5e2cfa01a93972b))


## v0.3.3 (2024-05-30)

### Fix

* fix: Add retries on server errors
* fix: pull config on ecs init ([`829e999`](https://github.com/Cloud-Technology-Office/cto-cli/commit/829e999057895c6cd60c26ede50d3cefbb2fd4c7))

### Unknown

* Merge pull request #11 from Cloud-Technology-Office/fixes ([`4a74c6b`](https://github.com/Cloud-Technology-Office/cto-cli/commit/4a74c6b0e8ce89b61f1ea0ea6d11fff6de23f785))


## v0.3.2 (2024-05-29)

### Fix

* fix: ask about email on ecs init ([`b500778`](https://github.com/Cloud-Technology-Office/cto-cli/commit/b5007785ef71d8b74a0d160487ce33615d32e3fe))

### Unknown

* Merge pull request #10 from Cloud-Technology-Office/email_fix ([`b254d9f`](https://github.com/Cloud-Technology-Office/cto-cli/commit/b254d9ff83767c5805ad8110c2aa48b1c636d631))


## v0.3.1 (2024-05-29)

### Fix

* fix: add email field for users ([`1b35f3b`](https://github.com/Cloud-Technology-Office/cto-cli/commit/1b35f3b26605467bfe2543ec69b973b47148f2f9))

### Unknown

* Merge pull request #9 from Cloud-Technology-Office/email_fix ([`22569e2`](https://github.com/Cloud-Technology-Office/cto-cli/commit/22569e20e0f7c0079ffe826faff7a252bac07d01))


## v0.3.0 (2024-05-29)

### Feature

* feat: Add support for `cto ecs config push --tag {tag}`, `cto ecs config build --config-id {config-id} --detect-drift` and new command `cto ecs config generate-schema`

* feat: validate json|yaml files before they get pushed to the server

* fix: display better schema errors ([`fd637b5`](https://github.com/Cloud-Technology-Office/cto-cli/commit/fd637b514f3e318d99f3e34e4da548479dedc709))

### Unknown

* Merge pull request #8 from Cloud-Technology-Office/development ([`ccf5c72`](https://github.com/Cloud-Technology-Office/cto-cli/commit/ccf5c72dca247db70f65fdf32d51e45ddb4ae73a))


## v0.2.0 (2024-05-03)

### Feature

* feat: Add support for ECS SaaS ([`c7e6963`](https://github.com/Cloud-Technology-Office/cto-cli/commit/c7e6963ae55725c9433cee757f4e1b6c6a126594))

### Unknown

* Merge pull request #6 from Cloud-Technology-Office/saas_support

Add support for ECS SaaS ([`632c43d`](https://github.com/Cloud-Technology-Office/cto-cli/commit/632c43ddd6a08d28b45887d52654dc8d7c407c93))


## v0.1.3 (2024-04-03)

### Fix

* fix: pypi repo field (#5) ([`1f61b43`](https://github.com/Cloud-Technology-Office/cto-cli/commit/1f61b436d62e9c1fdc1c34552fc421778d481bf6))

* fix: pypi package details (#4) ([`8f8a623`](https://github.com/Cloud-Technology-Office/cto-cli/commit/8f8a62393440db53b901a6f3f937745ad91355b1))


## v0.1.2 (2024-04-03)

### Build

* build: fix creating builds ([`0f64e3a`](https://github.com/Cloud-Technology-Office/cto-cli/commit/0f64e3a0fef98f9de3f7a0f8581829dfcdccd8b6))

### Fix

* fix: add python3.8 support (#2) ([`32c3986`](https://github.com/Cloud-Technology-Office/cto-cli/commit/32c3986496bef0046bcc45e4aa6922429e544c42))

### Unknown

* Merge pull request #3 from Cloud-Technology-Office/fix_build

build: fix builds ([`84c1171`](https://github.com/Cloud-Technology-Office/cto-cli/commit/84c11712f4c3f0ccf148a054924e2a63e617eaf2))


## v0.1.1 (2024-04-02)

### Unknown

* Release 0.1.1 (#1) ([`6e39638`](https://github.com/Cloud-Technology-Office/cto-cli/commit/6e39638f433ef8c068958692f64e0ebe06332502))

* Initial commit ([`43d9a1b`](https://github.com/Cloud-Technology-Office/cto-cli/commit/43d9a1bcca7ca498e5a13c5b8c6f1039a82c7b27))
