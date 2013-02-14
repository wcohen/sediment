Name:		sediment
Version:	0.1
Release:	1%{?dist}
Summary:	A function reordering toolset

License:	GPLv3+
URL:		
Source0:	

# sphinx is used for building documentation:
BuildRequires:  python-sphinx
Requires:	

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
%doc



%changelog
* Wed Fed 13 2013 William Cohen <wcohen@redhat.com> 0.1-1
- Initial release
