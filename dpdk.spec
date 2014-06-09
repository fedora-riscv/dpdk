%global rel 0.8

# As per packaging guidelines, since dpdk is pre-release, this is the git hash
# that I used with git archive to build the source tarball and the date on which
# I did it
%global upstreamtag 20140603git5ebbb1728

Name: dpdk
Version: 1.7.0 
Release: %{rel}.%{upstreamtag}%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{version}-%{upstreamtag}.tgz
Source1: defconfig_x86_64-default-linuxapp-gcc
Source2: defconfig_i686-default-linuxapp-gcc
Source3: common_linuxapp

#
# Currently the igb_uio module doesn't have a configuration option to disable
# itself in dpdk.  Since we don't build kernel modules as part of user space
# pacakges, this patch manually removes the Makefile directives to build it
# This can be dropped when upstream makes this configurable
#
Patch0: dpdk-1.7.0-igb_uio_disable.patch

Summary: Data Plane Development Kit core

#
# Note that, while this is dual licensed, all code that is included with this
# Pakcage are BSD licensed. The only files that aren't licensed via BSD is the
# kni kernel module which is dual LGPLv2/BSD, and thats not built for fedora.
#
License: BSD and LGPLv2 and GPLv2

#
# The DPDK is designed to optimize througput of network traffic using, among
# other techniques, carefully crafted x86 assembly instructions.  As such it
# currently (and likely never will) run on non-x86 platforms
#
ExclusiveArch: i386 x86_64 

%global target %{_arch}-default-linuxapp-gcc
%global machine default

BuildRequires: kernel-devel, kernel-headers, libpcap-devel, doxygen

%description
DPDK core includes kernel modules, core libraries and tools.
testpmd application allows to test fast packet processing environments
on x86 platforms. For instance, it can be used to check that environment
can support fast path applications such as 6WINDGate, pktgen, rumptcpip, etc.
More libraries are available as extensions in other packages.


%package devel
Summary: Data Plane Development Kit core for development
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
DPDK core-devel is a set of makefiles, headers, examples and documentation
for fast packet processing on x86 platforms.
More libraries are available as extensions in other packages.

%package doc
Summary: Data Plane Development Kit core programming API documentation
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
DPDK core library API programming documentation

%global destdir %{buildroot}%{_prefix}
%global datadir %{_datadir}/%{name}-%{version}
%global docdir  %{_docdir}/%{name}-%{version}

%prep
%setup -q
cp %{SOURCE1} ./config/
cp %{SOURCE2} ./config/
cp %{SOURCE3} ./config/
%patch0 -p1

%build
# need to enable debuginfo
export CPU_CFLAGS=-g
make V=1 O=%{target} T=%{target} %{?_smp_mflags} config
make V=1 O=%{target} %{?_smp_mflags}
make V=1 O=%{target} %{?_smp_mflags} doc

%install
make V=1   O=%{target}     DESTDIR=%{destdir}
mkdir -p                               %{buildroot}%{_sbindir}
mkdir -p                               %{buildroot}%{_libdir}/%{name}-%{version}
mkdir -p                               %{buildroot}%{_includedir}/%{name}-%{version}
mkdir -p                               %{buildroot}%{_bindir}
mv    %{destdir}/%{target}/app/testpmd %{buildroot}%{_bindir}/testpmd-%{version}
rmdir %{destdir}/%{target}/app
mv    %{destdir}/%{target}/include/*   %{buildroot}%{_includedir}/%{name}-%{version}
mv    %{destdir}/%{target}/lib/*       %{buildroot}%{_libdir}/%{name}-%{version}
mkdir -p                               %{buildroot}%{docdir}
mv    %{destdir}/%{target}/doc/*       %{buildroot}%{docdir}
rmdir %{destdir}/%{target}/doc
mkdir -p                               %{buildroot}%{datadir}
mv    %{destdir}/%{target}/.config     %{buildroot}%{datadir}/config
rm -rf %{destdir}/%{target}/kmod
mv    %{destdir}/%{target}             %{buildroot}%{datadir}
rm -rf %{destdir}/mk
rm -rf %{destdir}/scripts
cp -a            tools                 %{buildroot}%{datadir}

%files
# BSD
%dir %{datadir}
%{datadir}/config
# Theres no point in packaging any of the tools
# We currently don't need the igb uio script, there 
# are several uio scripts already available
# And the cpu_layout script functionality is 
# covered by lscpu
%exclude %{datadir}/tools
%{_bindir}/*
%{_libdir}/%{name}-%{version}

%files doc
#BSD
%{docdir}

%files devel
#BSD
%{_includedir}/*
#%{datadir}/%{target}
%exclude %{docdir}/html

%changelog
* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.0.7-0.8.20140603git5ebbb1728
- Fixed doc arch versioning issue

* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.0.7-0.7.20140603git5ebbb1728
- Added verbose output to build

* Tue May 13 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.0.7-0.6.20140603git5ebbb1728
- Initial Build

