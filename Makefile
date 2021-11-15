TESTS=tests
SETTINGS=tests.sqlite_settings

test:
	cd tests && DJANGO_SETTINGS_MODULE=$(SETTINGS) $(COVERAGE_COMMAND) ./manage.py test $(TESTS) --verbosity=2

coverage:
	+make test COVERAGE_COMMAND='coverage run --source=dol --branch'
	cd tests && coverage html

.PHONY: test
