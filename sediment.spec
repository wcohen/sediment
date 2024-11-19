Name:		sediment
Version:	0.9.3
Release:	1%{?dist}
Summary:	A function reordering tool set

License:	GPL-3.0-or-later
URL:		https://github.com/wcohen/sediment
Source0:	https://github.com/wcohen/sediment/archive/%{version}/%{name}-%{version}.tar.gz

# sphinx is used for building documentation:
BuildRequires: make
BuildRequires: python3-sphinx >= 2.0
BuildRequires: automake
BuildRequires: autoconf
#Requires: gcc-python3-plugin
Requires: python3dist(gv)
BuildArch: noarch

%description
The sediment tool set allows reordering of the functions in compiled
programs built with RPM to reduce the frequency of TLB misses and
decrease the number of pages in the resident set.  Sediment generates
call graphs from program execution and converts the call graphs into
link order information to improve code locality.

%prep
%autosetup -n sediment-%{version}


%build
autoreconf -iv
%configure
# doc makefile using sphinx does not work with parallel build
make

%install
%make_install


%files
%{_bindir}/gv2link
%{_bindir}/perf2gv
%{_bindir}/gen_profile_merge
%{_bindir}/make_sediment_rpmmacros
%{_libexecdir}/%{name}
%{_docdir}/sediment/html
%doc README AUTHORS NEWS COPYING
%{_mandir}/man1/*


%changelog
* Mon Nov 18 2024 William Cohen <wcohen@redhat.com> - 0.9.3-1
- Update documentation with Fedora 41 postgres example.

* Mon Nov 4 2024 William Cohen <wcohen@redhat.com> - 0.9.2-2
- Add make_sediment_rpmmacros and update Makefile.* and configure to include it.

* Mon Oct 21 2024 William Cohen <wcohen@redhat.com> - 0.9.2-1
- Update to use binutil 2.43 ld for linking.

* Tue Sep 10 2024 William Cohen <wcohen@redhat.com> - 0.9.1-17
- Incorporate Fedora sediment.spec fixes and general cleanup of sediment.spec.

* Mon Nov 05 2018 William Cohen <wcohen@redhat.com> - 0.9.1-2
- Use python3-sphinx to build documentation.

* Mon Nov 05 2018 William Cohen <wcohen@redhat.com> - 0.9.1-1
- Use python3.

* Fri May 18 2018 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0.9-3
- Update graphviz dependency

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
