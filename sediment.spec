Name:		sediment
Version:	0.6
Release:	1%{?dist}
Summary:	A function reordering tool set

Group:		Development/Tools
License:	GPLv3+
URL:		https://fedorahosted.org/sediment/
Source0:	https://fedorahosted.org/releases/s/e/sediment/sediment-%{version}.tar.gz

# sphinx is used for building documentation:
BuildRequires: python-sphinx
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
make %{?_smp_mflags}

%install
%make_install


%files
%{_bindir}/gv2link
%{_bindir}/perf2gv
%{_libexecdir}/%{name}
%doc %{_docdir}
%doc README AUTHORS NEWS COPYING
%{_mandir}/man1/*


%changelog
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
