Name:		sediment
Version:	0.1
Release:	2%{?dist}
Summary:	A function reordering toolset

License:	GPLv3+
URL:		http://people.redhat.com/wcohen/sediment
Source0:	%{name}-%{version}.tar.gz

# sphinx is used for building documentation:
BuildRequires:  python-sphinx
#Requires: gcc-python3-plugin
Requires: graphviz-python
BuildArch: noarch

%description
sediment is a set of programs that allow one reorder the functions in
an executable based on statical and dynamic information about the program
execution.


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
%{_bindir}/gv2link.py
%{_bindir}/perf2gv.py
%{_bindir}/write-dot-callgraph.py
%doc %{_datadir}/doc/%{name}/html
%doc README AUTHORS NEWS COPYING


%changelog
* Tue Feb 18 2014 William Cohen <wcohen@redhat.com> 0.1-2
- Add graphviz-python requires.

* Thu Feb 14 2013 William Cohen <wcohen@redhat.com> 0.1-1
- Initial release
