# Add option to build as static libraries (--without shared)
%bcond_without shared
# Add option to build without examples
%bcond_without examples
# Add option to build without tools
%bcond_without tools
# Add option to build the PDF documentation separately (--with pdfdoc)
%bcond_with pdfdoc


Name: dpdk
Version: 2.2.0
Release: 1%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{version}.tar.gz

Patch1: enic-pun-fix.patch
Patch2: dpdk-2.2-dtneeded.patch
Patch4: dpdk-2.2-examples.patch

Summary: Set of libraries and drivers for fast packet processing

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
ExclusiveArch: x86_64 

%define machine native

%define target x86_64-%{machine}-linuxapp-gcc



BuildRequires: kernel-headers, libpcap-devel, doxygen, python-sphinx, zlib-devel
%if %{with pdfdoc}
BuildRequires: texlive-dejavu inkscape texlive-latex-bin-bin
BuildRequires: texlive-kpathsea-bin texlive-metafont-bin texlive-cm
BuildRequires: texlive-cmap texlive-ec texlive-babel-english
BuildRequires: texlive-fancyhdr texlive-fancybox texlive-titlesec
BuildRequires: texlive-framed texlive-threeparttable texlive-mdwtools
BuildRequires: texlive-wrapfig texlive-parskip texlive-upquote texlive-multirow
BuildRequires: texlive-helvetic texlive-times texlive-dvips
%endif

%description
The Data Plane Development Kit is a set of libraries and drivers for
fast packet processing in the user space.

%package devel
Summary: Data Plane Development Kit development files
Requires: %{name}%{?_isa} = %{version}-%{release}
%if ! %{with shared}
Provides: %{name}-static = %{version}-%{release}
%endif

%description devel
This package contains the headers and other files needed for developing
applications with the Data Plane Development Kit.

%package doc
Summary: Data Plane Development Kit API documentation
BuildArch: noarch

%description doc
API programming documentation for the Data Plane Development Kit.

%if %{with tools}
%package tools
Summary: Tools for setting up Data Plane Development Kit environment
Requires: %{name} = %{version}-%{release}
Requires: kmod pciutils findutils iproute

%description tools
%{summary}
%endif

%if %{with examples}
%package examples
Summary: Data Plane Development Kit example applications
BuildRequires: libvirt-devel

%description examples
Example applications utilizing the Data Plane Development Kit, such
as L2 and L3 forwarding.
%endif

%define sdkdir  %{_libdir}/%{name}-%{version}-sdk
%define docdir  %{_docdir}/%{name}-%{version}

%prep
%setup -q
%patch1 -p2 -z .enic
%patch2 -p1 -z .dtneeded
%patch4 -p1 -z .examples

%build
# set up a method for modifying the resulting .config file
function setconf() {
	if grep -q $1 %{target}/.config; then
		sed -i "s:^$1=.*$:$1=$2:g" %{target}/.config
	else
		echo $1=$2 >> %{target}/.config
	fi
}

# In case dpdk-devel is installed, we should ignore its hints about the SDK directories
unset RTE_SDK RTE_INCLUDE RTE_TARGET

# For the release, '-Wno-error=array-bounds' is done to prevent a spurious error
# generated by gcc 5.X against the 2.1 branch
export EXTRA_CFLAGS="%{optflags} -Wformat -fPIC -Wno-error=array-bounds"

# DPDK defaults to using builder-specific compiler flags.  However,
# the config has been changed by specifying CONFIG_RTE_MACHINE=default
# in order to build for a more generic host.  NOTE: It is possible that
# the compiler flags used still won't work for all Fedora-supported
# machines, but runtime checks in DPDK will catch those situations.

make V=1 O=%{target} T=%{target} %{?_smp_mflags} config

setconf CONFIG_RTE_MACHINE "default"
# Disable experimental features
setconf CONFIG_RTE_NEXT_ABI n
setconf CONFIG_RTE_LIBRTE_CRYPTODEV n
setconf CONFIG_RTE_LIBRTE_MBUF_OFFLOAD n

setconf CONFIG_RTE_LIBRTE_BNX2X_PMD y
setconf CONFIG_RTE_LIBRTE_PMD_PCAP y
setconf CONFIG_RTE_LIBRTE_VHOST y

setconf CONFIG_RTE_EAL_IGB_UIO n
setconf CONFIG_RTE_LIBRTE_KNI n
setconf CONFIG_RTE_KNI_KMOD n
setconf CONFIG_RTE_KNI_PREEMPT_DEFAULT n

%if %{with shared}
setconf CONFIG_RTE_BUILD_SHARED_LIB y
%endif

make V=1 O=%{target} %{?_smp_mflags}
make V=1 O=%{target} %{?_smp_mflags} doc-api-html doc-guides-html %{?with_pdfdoc: guides-pdf}

%if %{with examples}
make V=1 O=%{target}/examples T=%{target} %{?_smp_mflags} examples
%endif

%install

# DPDK's "make install" seems a bit broken -- do things manually...

mkdir -p                     %{buildroot}%{_bindir}
cp -a  %{target}/app/testpmd %{buildroot}%{_bindir}/testpmd
mkdir -p                     %{buildroot}%{_includedir}/%{name}-%{version}
cp -Lr  %{target}/include/*   %{buildroot}%{_includedir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{_libdir}
cp -a  %{target}/lib/*       %{buildroot}%{_libdir}
mkdir -p                     %{buildroot}%{docdir}
cp -a  %{target}/doc/*       %{buildroot}%{docdir}

%if %{with shared}
libext=so
%else
libext=a
%endif

# DPDK apps expect a particular (and somewhat peculiar) directory layout
# for building, arrange for that
mkdir -p                     %{buildroot}%{sdkdir}/%{target}
mkdir -p                     %{buildroot}%{sdkdir}/lib
cp -a  %{target}/.config     %{buildroot}%{sdkdir}/%{target}
ln -s  ../lib %{buildroot}%{sdkdir}/%{target}/lib
ln -s  ../../include/%{name}-%{version} %{buildroot}%{sdkdir}/include
ln -s  ../../../include/%{name}-%{version} %{buildroot}%{sdkdir}/%{target}/include
cp -a  mk/                   %{buildroot}%{sdkdir}
mkdir -p                     %{buildroot}%{sdkdir}/scripts
cp -a scripts/*.sh           %{buildroot}%{sdkdir}/scripts

# Create library symlinks for the "sdk"
for f in %{buildroot}/%{_libdir}/*.${libext}; do
    l=`basename ${f}`
    ln -s ../../${l} %{buildroot}%{sdkdir}/lib/${l}
done

%if %{with tools}
cp -p tools/*.py             %{buildroot}%{_bindir}
%endif

%if %{with examples}
find %{target}/examples/ -name "*.map" | xargs rm -f
for f in %{target}/examples/*/%{target}/app/*; do
    bn=`basename ${f}`
    cp -p ${f} %{buildroot}%{_bindir}/dpdk_example_${bn}
done
mkdir -p                     %{buildroot}%{_datadir}/%{name}-%{version}
cp -a examples/              %{buildroot}%{_datadir}/%{name}-%{version}
%endif

# Setup RTE_SDK environment as expected by apps etc
mkdir -p %{buildroot}/%{_sysconfdir}/profile.d
cat << EOF > %{buildroot}/%{_sysconfdir}/profile.d/dpdk-sdk-%{_arch}.sh
if [ -z "\${RTE_SDK}" ]; then
    export RTE_SDK="%{sdkdir}"
    export RTE_TARGET="%{target}"
    export RTE_INCLUDE="%{_includedir}/%{name}-%{version}"
fi
EOF

cat << EOF > %{buildroot}/%{_sysconfdir}/profile.d/dpdk-sdk-%{_arch}.csh
if ( ! \$RTE_SDK ) then
    setenv RTE_SDK "%{sdkdir}"
    setenv RTE_TARGET "%{target}"
    setenv RTE_INCLUDE "%{_includedir}/%{name}-%{version}"
endif
EOF

# Theres no point in packaging any of the tools
# We currently don't need the igb uio script, there
# are several uio scripts already available
# And the cpu_layout script functionality is
# covered by lscpu
#cp -a  tools                 %{buildroot}%{datadir}

# Fixup irregular modes in headers
find %{buildroot}%{_includedir}/%{name}-%{version} -type f | xargs chmod 0644

# Upstream has an option to build a combined library but it's bloatware which
# wont work at all when library versions start moving, replace it with a
# linker script which avoids these issues. Linking against the script during
# build resolves into links to the actual used libraries which is just fine
# for us, so this combined library is a build-time only construct now.

comblib=libdpdk.${libext}

echo "GROUP (" > ${comblib}
find %{buildroot}/%{_libdir}/ -name "*.${libext}" |\
	sed -e "s:^%{buildroot}/:  :g" >> ${comblib}
echo ")" >> ${comblib}
install -m 644 ${comblib} %{buildroot}/%{_libdir}/${comblib}

%files
# BSD
%{_bindir}/*
%exclude %{_bindir}/*.py
%exclude %{_bindir}/dpdk_example_*
%if %{with shared}
%{_libdir}/*.so.*
%{_libdir}/*_pmd_*.so
%{_libdir}/*_pmd_*.so.*
%endif

%files doc
#BSD
%{docdir}

%files devel
#BSD
%{_includedir}/*
%{sdkdir}
%{_sysconfdir}/profile.d/dpdk-sdk-*.*
%if ! %{with shared}
%{_libdir}/*.a
%else
%{_libdir}/*.so
%exclude %{_libdir}/*_pmd_*.so
%exclude %{_libdir}/*_pmd_*.so.*
%endif

%if %{with tools}
%files tools
%{_bindir}/*.py
%endif

%if %{with examples}
%files examples
%{_bindir}/dpdk_example_*
%exclude %{_bindir}/*.py
%{_datadir}/%{name}-%{version}/examples
%endif

%changelog
* Wed Jan 20 2016 Panu Matilainen <pmatilai@redhat.com> - 2.2.0-1
- Update to 2.2.0

* Thu Oct 22 2015 Aaron Conole <aconole@redhat.com> - 2.1.0-3
- Include examples binaries
- Enable the Broadcom NetXtreme II 10Gb PMD
- Fix up linkages for the dpdk-devel package

* Wed Sep 30 2015 Aaron Conole <aconole@redhat.com> - 2.1.0-2
- Re-enable the IGB, IXGBE, I40E PMDs
- Bring the Fedora and RHEL packages more in-line.

* Wed Aug 26 2015 Neil Horman <nhorman@redhat.com> - 2.1.0-1
- Update to latest version

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Apr 06 2015 Neil Horman <nhorman@redhat.com> - 2.0.0-1
- Update to dpdk 2.0
- converted --with shared option to --without shared option

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-8
- Always build with -fPIC

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-7
- Policy compliance: move static libraries to -devel, provide dpdk-static
- Add a spec option to build as shared libraries

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-6
- Avoid variable expansion in the spec here-documents during build
- Drop now unnecessary debug flags patch
- Add a spec option to build a combined library

* Tue Jan 27 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-5
- Avoid unnecessary use of %%global, lazy expansion is normally better
- Drop unused destdir macro while at it
- Arrange for RTE_SDK environment + directory layout expected by DPDK apps
- Drop config from main package, it shouldn't be needed at runtime

* Tue Jan 27 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-4
- Copy the headers instead of broken symlinks into -devel package
- Force sane mode on the headers
- Avoid unnecessary %%exclude by not copying unpackaged content to buildroot
- Clean up summaries and descriptions
- Drop unnecessary kernel-devel BR, we are not building kernel modules

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 17 2014 - John W. Linville <linville@redhat.com> - 1.7.0-2
- Use EXTRA_CFLAGS to include standard Fedora compiler flags in build
- Set CONFIG_RTE_MACHINE=default to build for least-common-denominator machines
- Turn-off build of librte_acl, since it does not build on default machines
- Turn-off build of physical device PMDs that require kernel support
- Clean-up the install rules to match current packaging
- Correct changelog versions 1.0.7 -> 1.7.0
- Remove ix86 from ExclusiveArch -- it does not build with above changes

* Thu Jul 10 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-1.0
- Update source to official 1.7.0 release 

* Thu Jul 03 2014 - Neil Horman <nhorman@tuxdriver.com>
- Fixing up release numbering

* Tue Jul 01 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.9.1.20140603git5ebbb1728
- Fixed some build errors (empty debuginfo, bad 32 bit build)

* Wed Jun 11 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.9.20140603git5ebbb1728
- Fix another build dependency

* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.8.20140603git5ebbb1728
- Fixed doc arch versioning issue

* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.7.20140603git5ebbb1728
- Added verbose output to build

* Tue May 13 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.6.20140603git5ebbb1728
- Initial Build

