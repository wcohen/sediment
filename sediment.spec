Name:		sediment
Version:	0.9
Release:	2%{?dist}
Summary:	A function reordering tool set

Group:		Development/Tools
License:	GPLv3+
URL:		https://github.com/wcohen/sediment
# rpmbuild doesn't like it, but actual GitHub URL is:
# https://github.com/wcohen/sediment/archive/%%{version}.tar.gz
Source0:	https://github.com/wcohen/sediment/archive/sediment-%{version}.tar.gz

# sphinx is used for building documentation:
BuildRequires: python2-sphinx
BuildRequires: automake
#Requires: gcc-python3-plugin
Requires: graphviz-python
BuildArch: noarch

%description
The sediment tool set allows reordering of the functions in compiled
programs built with RPM to reduce the frequency of TLB misses and
decrease the number of pages in the resident set.  Sediment generates
call graphs from program execution and converts the call graphs into
link order information to improve code locality.

%prep
%setup -q


%build
%configure
# doc makefile using sphinx does not work with parallel build
make

%install
%make_install


%files
%{_bindir}/gv2link
%{_bindir}/perf2gv
%{_bindir}/gen_profile_merge
%{_libexecdir}/%{name}
%{_docdir}/sediment/html
%doc README AUTHORS NEWS COPYING
%{_mandir}/man1/*


%changelog
* Wed Mar 07 2018 William Cohen <wcohen@redhat.com> - 0.9-2
- Add automake build requires.

* Wed Mar 07 2018 William Cohen <wcohen@redhat.com> - 0.9-1
- Rebuild on sediment 0.9.

* Wed Mar 05 2014 William Cohen <wcohen@redhat.com> 0.8-2
- Avoid listing doc files twice in newer Fedora distributions.

* Wed Mar 05 2014 William Cohen <wcohen@redhat.com> 0.8-1
- Rebase on sediment-0.7.

* Mon Mar 03 2014 William Cohen <wcohen@redhat.com> 0.7-1
- Rebase on sediment-0.7.

* Fri Feb 28 2014 William Cohen <wcohen@redhat.com> 0.6-1
- Update package and spec file based on Fedora package review rhbz 1070449.

* Thu Feb 27 2014 William Cohen <wcohen@redhat.com> 0.5-2
- Update spec file based on Fedora package review rhbz 1070449.

* Wed Feb 26 2014 William Cohen <wcohen@redhat.com> 0.5-1
- Bump version.

* Wed Feb 26 2014 William Cohen <wcohen@redhat.com> 0.4-1
- Bump version.

* Wed Feb 26 2014 William Cohen <wcohen@redhat.com> 0.3-3
- Move write-dot-callgraph.py out of /usr/bin.

* Mon Feb 24 2014 William Cohen <wcohen@redhat.com> 0.3-2
- spec file fixes based on comments.

* Mon Feb 24 2014 William Cohen <wcohen@redhat.com> 0.3-1
- Bump version.

* Mon Feb 24 2014 William Cohen <wcohen@redhat.com> 0.2-3
- Add basic man pages for perf2gv.py and gv2link.py.

* Wed Feb 19 2014 William Cohen <wcohen@redhat.com> 0.2-1
- Bump version to 0.2.

* Tue Feb 18 2014 William Cohen <wcohen@redhat.com> 0.1-2
- Add graphviz-python requires.

* Thu Feb 14 2013 William Cohen <wcohen@redhat.com> 0.1-1
- Initial release
