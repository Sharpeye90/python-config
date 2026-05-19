%{!?__python3: %global __python3 /usr/bin/python3}

%bcond_without tests

%global project_name pcore
%global project_description %{expand:
Python configuration files themselves are actual Python files. The module
reads only values in uppercase from them, checks that they contain only basic
Python types and returns a dictionary which corresponds to the configuration
file.

Note: if you want to validate the configuration values, take a look at
https://github.com/KonishchevDmitry/object-validator project.}

Name:    python-config
Version: 1.0.0
Release: ROCKIT1%{?dist}
Summary: A simple module for reading Python configuration files

Group:   Development/Libraries
License: GPLv3
URL:     https://github.com/KonishchevDmitry/python-config
Source:  http://pypi.python.org/packages/source/p/python-config/python-config-%version.tar.gz

BuildArch:     noarch
BuildRequires: make

%description %{project_description}


%package -n python%{python3_pkgversion}-config
Summary: %{summary}
BuildRequires: python%{python3_pkgversion}-devel
BuildRequires: python%{python3_pkgversion}-setuptools
%if 0%{with tests}
BuildRequires: python3-dataclasses
BuildRequires: python%{python3_pkgversion}-pytest >= 2.2.4
%endif  # with tests
Requires:  python3-dataclasses
Obsoletes: python36-config
Conflicts: python36-config

%description -n python%{python3_pkgversion}-config %{project_description}


%prep
%setup -n %name-%version -q


%build
%py3_build


%check
make PYTHON=%{__python3} check


%install
%py3_install


%files -n python%{python3_pkgversion}-config
%defattr(-,root,root,-)
%{python3_sitelib}/python_config/
%{python3_sitelib}/python_config/__pycache__/
%{python3_sitelib}/python_config-%{version}-*.egg-info
%doc ChangeLog INSTALL README.rst


%clean
[ "%buildroot" = "/" ] || rm -rf "%buildroot"


%changelog
* Tue Jan 24 2023 Andrey Kulaev <adkulaev@gmail.com> - 0.1.2-4
- Add centos 8.4 support

* Sun Feb 10 2019 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.2-3
- Enable tests for python36

* Sun Jan 13 2019 Mikhail Ushanov <gm.mephisto@gmail.com> - 0.1.2-2
- Add python3 package build for EPEL

* Mon Dec 12 2016 Dmitry Konishchev <konishchev@gmail.com> - 0.1.2-1
- New version.

* Wed Jul 03 2013 Dmitry Konishchev <konishchev@gmail.com> - 0.1.1-1
- New version.

* Wed Jul 03 2013 Dmitry Konishchev <konishchev@gmail.com> - 0.1-1
- New package.
