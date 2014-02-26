Name:		sediment
Version:	0.3
Release:	2%{?dist}
Summary:	A function reordering tool set

Group:		Development/Tools
License:	GPLv3+
URL:		http://people.redhat.com/wcohen/sediment
Source0:	http://people.redhat.com/wcohen/sediment/%{name}-%{version}.tar.gz

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
rm -rf $RPM_BUILD_ROOT
%make_install


%files
%defattr(-,root,root,-)
%{_bindir}/gv2link
%{_bindir}/perf2gv
%{_bindir}/write-dot-callgraph.py
%doc %{_datadir}/doc/%{name}/html
%doc README AUTHORS NEWS COPYING
%doc %{_mandir}/man1/*


%changelog
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
