%define with_gcov  %{?_with_gcov:1} %{?!_with_gcov:0}
%define with_san  %{?_with_san:1} %{?!_with_san:0}
%define with_ub %{?_with_ub:1} %{?!_with_ub:0}
%if !%{with_gcov}
%define debug_package %{nil}
%endif
Name:           custom_build_tool
Summary:        custom build tool for obs
License:        GPL
Group:          System/Management
Version:        1.0
Release:        18
BuildRoot:      %{_tmppath}/%{name}-%{version}
Source0:        %{name}-%{version}.tar.bz2
BuildRequires:  util-linux coreutils
BuildRequires: -custom_build_tool-nocheck
BuildRequires: -obs-env
BuildRequires: -gcc_secure
BuildRequires: -bep-env
BuildRequires: -custom_build_tool-gcov
BuildRequires: -custom_build_tool-san
BuildRequires: -custom_build_tool-uploadbuild

Requires:       bash rpm-build rpm-sign sed util-linux coreutils gnupg2
%description
provide other method to deal parameter passing for OBS build

%package nocheck
Group: Development/Libraries
BuildArch: noarch
Requires:bash rpm-build sed util-linux coreutils
Requires:custom_build_tool
Summary: add nocheck to rpmbuild

%description nocheck

%package nodebug
Group: Development/Libraries
BuildArch: noarch
Requires:bash rpm-build sed util-linux coreutils
Requires:custom_build_tool
Summary:  change debug error to warning for rpmbuild

%description nodebug

%package target
Group: Development/Libraries
BuildArch: noarch
Requires:bash rpm-build sed util-linux coreutils
Requires:custom_build_tool
Summary: add target to rpmbuild

%description target

%package gcov
Group:Development/Libraries
Requires:util-linux rpm grep binutils gcc coreutils rpm-build
Requires:custom_build_tool
BuildRequires:util-linux coreutils
Summary:Build with gcov

%description gcov

%package uploadbuild
Group:Development/Libraries
Requires:util-linux rpm grep binutils gcc coreutils rpm-build pbzip2
Requires:custom_build_tool
BuildRequires:util-linux coreutils
Summary:Collect the rmpbuild/BUILD directory

%description uploadbuild
Collect the rmpbuild/BUILD directory and upload it to the specified server

%package san
Group:Development/Libraries
Requires:util-linux rpm grep binutils gcc coreutils rpm-build
Requires:custom_build_tool
Requires:gcc_secure
BuildRequires:util-linux coreutils
Summary:Build with san

%description san


%package gcov-server
Group:Development/Libraries
Requires:util-linux rpm grep binutils gcc coreutils rpm-build
BuildRequires:util-linux coreutils
Summary:gcov file transfer server

%description gcov-server



%prep
%setup -c

%build


%install
mkdir -p %{buildroot}/opt/
mkdir -p %{buildroot}/opt/custom_build_tool
mkdir -p %{buildroot}/home/abuild/.gnupg/
mkdir -p %{buildroot}/root/.gnupg/
install -m 700 %{name}-%{version}/*.sh %{buildroot}/opt/custom_build_tool/
install -m 600 %{name}-%{version}/rpmbuild-nocheck %{buildroot}/opt/custom_build_tool/
install -m 600 %{name}-%{version}/rpmbuild-target %{buildroot}/opt/custom_build_tool/
%if %{with_gcov}
install -m 600 %{name}-%{version}/rpmbuild-gcov %{buildroot}/opt/custom_build_tool/
%endif
%if %{with_san}
install -m 600 %{name}-%{version}/rpmbuild-san %{buildroot}/opt/custom_build_tool/
%endif
%if %{with_ub}
install -m 600 %{name}-%{version}/rpmbuild-ub %{buildroot}/opt/custom_build_tool/
%endif


%post
bash /opt/custom_build_tool/custom_build_tool.sh
%post nocheck
sed -i '/####add parameter start/r /opt/custom_build_tool/rpmbuild-nocheck' /usr/bin/rpmbuild
%post nodebug
sed -i 's/strict=true/strict=false/' /usr/lib/rpm/find-debuginfo.sh
%post target
sed -i '/####add parameter start/r /opt/custom_build_tool/rpmbuild-target' /usr/bin/rpmbuild
echo "abuild ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

%if %{with_gcov}
%post gcov
cp -a /usr/bin/mv /usr/bin/gmv
chmod 4777 /usr/bin/gmv
sed -i '/####add parameter start/r /opt/custom_build_tool/rpmbuild-gcov' /usr/bin/rpmbuild
old_gcc=/usr/bin/gcc
old_gplus=/usr/bin/g++
old_rpmbuild=/usr/bin/rpmbuild
old_cplus=/usr/bin/c++

cat <<END1 > ${old_rpmbuild}-gcov
#!/bin/sh -x

${old_rpmbuild} "\$@"
ret=\$?

if [ \$ret -eq 0 ]; then
    source /opt/custom_build_tool/upload.sh
    echo "Gcov version has been compiled"
else
    if file /usr/bin/gcc | grep ELF; then
        exit \$ret
    else
        /usr/bin/gmv ${old_gcc}_gcov $old_gcc
        /usr/bin/gmv ${old_gplus}_gcov $old_gplus
        if [ -d /home/abuild/rpmbuild/BUILD ]; then
            rm -rf /home/abuild/rpmbuild/BUILD
            rm -rf /home/abuild/rpmbuild/BUILDROOT
        else
            rm -rf /root/rpmbuild/BUILD
            rm -rf /root/rpmbuild/BUILDROOT
        fi

         ${old_rpmbuild} "\$@"
         ret=\$?
         if [ \$ret -eq 0 ]; then
            source /opt/custom_build_tool/upload.sh
         else
            exit \$ret
         fi
     fi
fi
END1
chmod 755 ${old_rpmbuild}-gcov

# add gcc args
mv $old_gcc $old_gcc"_gcov"
cat <<END1 > $old_gcc
#!/bin/sh -x


echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
    ${old_gcc}_gcov "\$@"
else
    ${old_gcc}_gcov  %{?_with_gcov_args}  "\$@"
fi


END1
chmod 755 $old_gcc $old_gcc"_gcov"

# add gplus args
if [ -f $old_gplus ]; then
    mv $old_gplus $old_gplus"_gcov"
cat <<END1 > $old_gplus
#!/bin/sh -x


echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
        ${old_gplus}_gcov "\$@"
else
        ${old_gplus}_gcov %{?_with_gcov_args}  "\$@"
fi

END1
    chmod 755 $old_gplus $old_gplus"_gcov"
fi

# add cplus args
if [ -f $old_cplus ]; then
    mv $old_cplus $old_cplus"_gcov"
cat <<END1 > $old_cplus
#!/bin/sh

echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
    ${old_cplus}_gcov "\$@"
else
    ${old_cplus}_gcov %{?_with_gcov_args}  "\$@"
fi

END1
    chmod 755 $old_cplus $old_cplus"_gcov"
fi
%endif

%if %{with_ub}
%post uploadbuild
sed -i '/####add parameter start/r /opt/custom_build_tool/rpmbuild-ub' /usr/bin/rpmbuild
bin_rpmbuild=/usr/bin/rpmbuild
cmd_rpmbuild=/usr/bin/rpmbuild-ub

cat <<END1 > ${cmd_rpmbuild}
#!/bin/sh -x

    ${bin_rpmbuild} "\$@"
    ret=\$?
    if [ \$ret -ne 0 ]; then
        exit \$ret
    fi
    source /opt/custom_build_tool/upload_build.sh
END1
chmod 755 ${cmd_rpmbuild}
%endif


%if %{with_san}
%post san
cp -a /usr/bin/mv /usr/bin/gmv
chmod 4777 /usr/bin/gmv
sed -i '/####add parameter start/r /opt/custom_build_tool/rpmbuild-san' /usr/bin/rpmbuild
old_gcc=/usr/bin/gcc
old_gplus=/usr/bin/g++
old_rpmbuild=/usr/bin/rpmbuild
old_cplus=/usr/bin/c++
ulimit -v unlimited
ulimit -a
sed '2 i export ASAN_OPTIONS=abort_on_error=0:disable_coredump=0:detect_leaks=0\nexport LD_PRELOAD=/usr/lib64/libasan.so.4' -i /usr/lib/rpm/find-debuginfo.sh
head /usr/lib/rpm/find-debuginfo.sh

sed -i  "$ a* hard as unlimited\n* soft as unlimited" /etc/security/limits.conf
cat <<END1 > ${old_rpmbuild}-san
#!/bin/sh -x
ulimit -v unlimited
ulimit -a
export ASAN_OPTIONS=detect_leaks=0:halt_on_error=0

${old_rpmbuild} "\$@"

ret=\$?
echo "SAN version has been compiled"
exit \$ret

END1
chmod 755 ${old_rpmbuild}-san

# add gcc args
mv $old_gcc $old_gcc"_san"
cat <<END1 > $old_gcc
#!/bin/sh


echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
    ${old_gcc}_san "\$@"
else
    ${old_gcc}_san  %{?_with_san_args}  "\$@"
fi


END1
chmod 755 $old_gcc $old_gcc"_san"

# add gplus args
if [ -f $old_gplus ]; then
    mv $old_gplus $old_gplus"_san"
cat <<END1 > $old_gplus
#!/bin/sh


echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
        ${old_gplus}_san "\$@"
else
        ${old_gplus}_san %{?_with_san_args}  "\$@"
fi

END1
    chmod 755 $old_gplus $old_gplus"_san"
fi

# add cplus args
if [ -f $old_cplus ]; then
    mv $old_cplus $old_cplus"_san"
cat <<END1 > $old_cplus
#!/bin/sh


echo "\$@" | grep conftest &>/tmp/tmp.tmp
ret=\$?
if [ \$ret -eq 0 ]; then
    ${old_cplus}_san "\$@"
else
    ${old_cplus}_san %{?_with_san_args}  "\$@"
fi

END1
    chmod 755 $old_cplus $old_cplus"_san"
fi
%endif



%preun

%postun
rm -rf /opt/custom_build_tool/custom_build_tool.sh
%postun nocheck
rm -rf /opt/custom_build_tool/rpmbuild-nocheck
%postun target
rm -rf /opt/custom_build_tool/rpmbuild-target
%if %{with_gcov}
%postun gcov
rm -rf /opt/custom_build_tool/rpmbuild-gcov
%endif
%if %{with_san}
%postun san
rm -rf /opt/custom_build_tool/rpmbuild-san
%endif
%if %{with_ub}
%postun uploadbuild
rm -rf /opt/custom_build_tool/rpmbuild-ub
%endif

%files
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/custom_build_tool.sh

%files nocheck
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/rpmbuild-nocheck

%files nodebug
%defattr(-,root,root)

%if %{with_gcov}
%files gcov
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/rpmbuild-gcov
/opt/custom_build_tool/upload.sh
/opt/custom_build_tool/client-tool-linux
/opt/custom_build_tool/cmdlist

%files gcov-server
%defattr(-,root,root)
%dir /opt/custom_build_tool
/opt/custom_build_tool/server-tool-linux
/opt/custom_build_tool/config.ini
%endif

%if %{with_ub}
%files uploadbuild
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/rpmbuild-ub
/opt/custom_build_tool/upload_build.sh
/opt/custom_build_tool/client-tool-linux
/opt/custom_build_tool/cmdlist
%endif

%if %{with_san}
%files san
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/rpmbuild-san
%endif

%files target
%defattr(-,root,root)
%dir /opt
%dir /opt/custom_build_tool
/opt/custom_build_tool/rpmbuild-target

%clean
rm -rf $RPM_BUILD_ROOT/*
rm -rf %{_tmppath}/%{name}-%{version}
rm -rf $RPM_BUILD_DIR/%{name}-%{version}

%changelog
* Tue Jul 14 2020 Buildteam <buildteam@openeuler.org> - 1.0-18
- package init