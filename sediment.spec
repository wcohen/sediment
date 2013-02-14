Name:		sediment
Version:	0.1
Release:	1%{?dist}
Summary:	A function reordering toolset

License:	GPLv3+
URL:		http://people.redhat.com/wcohen/sediment
Source0:	%{name}-%{version}.tar.gz

# sphinx is used for building documentation:
BuildRequires:  python-sphinx

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
%doc



%changelog
* Thu Feb 14 2013 William Cohen <wcohen@redhat.com> 0.1-1
- Initial release
