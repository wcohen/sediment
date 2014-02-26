# Makefile.am for sediment
# W. E. Cohen

#
DEBUG= -g
OPTIMIZE=
CCFLAGS=-Wall $(DEBUG) $(OPTIMIZE)

dist_bin_SCRIPTS = perf2gv gv2link write-dot-callgraph.py
EXTRA_DIST = sediment.spec


SUBDIRS = docs
DIST_SUBDIRS = $(SUBDIRS)

clean-local:
	rm -f *.gcov *.gcno *.gcda ${PACKAGE_TARNAME}-*.tar.gz
	rm -rf ${PACKAGE_TARNAME}-${PACKAGE_VERSION}
	rm -rf $(TEST_COV_DIR)

.PHONY:

rpm: dist
	mkdir -p `rpm --eval %_specdir`
	mkdir -p `rpm --eval %_srcrpmdir`
	mkdir -p `rpm --eval %_rpmdir`
	mkdir -p `rpm --eval %_builddir`
	mkdir -p `rpm --eval %_buildroot`
	rpmbuild --define "_sourcedir $(PWD)/" -ta \
		${PACKAGE_TARNAME}-${PACKAGE_VERSION}.tar.gz $(RPMBUILDFLAGS)
