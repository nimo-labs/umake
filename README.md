![Build status](https://github.com/nimo-labs/umake/actions/workflows/build_lin_stable.yml/badge.svg)
![Build status](https://github.com/nimo-labs/umake/actions/workflows/build_win_stable.yml/badge.svg)
![Build status](https://github.com/nimo-labs/umake/actions/workflows/build_lin.yml/badge.svg?branch=dev)
![Build status](https://github.com/nimo-labs/umake/actions/workflows/build_win.yml/badge.svg?branch=dev)
# umake
**Micro-controller build manager**
Released under GPL3, umake (pronounced micro make) is a utility to streamline the creation of micro-controller firmware projects and allow support for cross platform libraries.
Although the initial intention is to create projects for bare metal micro controllers such as Microchip PIC and SAM processors the potential exists to extend it to larger projects such as embedded linux targets.

One of the key aims of umake is to allow underlying libraries to present common API  whilst allowing compile time selection of drivers based on the target.

# Concept
A umake project starts with a single json file called umakefile. This is parsed by umake so automatically clone / pull source code from git repositories and generate the appropriate Makefile for the project.

umake does include a clean command which cleans all temporary files, however as it also removes downloaded repositories it is recommended that you add the appropriate entries to .gitignore (or equivalent) to minimise bandwith.

## .gitignore
It is recommended that you add the following lines to your .gitignore (or equivalent file) if using version control for your project:

Makefile
build/*
umake/*

# umakefile
## Required fields
### target
### buildDir
### microcontroller
### toolchain
### libraries
#### Required fields
#### Optional fields
##### checkout
##### branch
##### books
## Optional fields
### linkerFile
### c_sources
### cpp_sources
### includes
### defines
### cflags
### ldflags