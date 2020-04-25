/*
 * This file is part of the umake distribution (https://github.com/nimo-labs/umake).
 * Copyright (c) 2020 Nimolabs Ltd. www.nimo.uk
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "rapidjson/document.h"     // rapidjson's DOM-style API
#include "rapidjson/prettywriter.h" // for stringify JSON
#include "rapidjson/istreamwrapper.h"
#include "rapidjson/error/en.h"
#include <cstdio>
#include <string>
#include <fstream>
#include <iostream>
#include <sys/stat.h> /*mkdir */
#include <unistd.h>   /*chdir */

#include "umake.h"
#include "boilerplate.h"
#include "parseMicrocontroller.h"
#include "processTargets.h"

#define JSON_INT 0
#define JSON_STRING 1

rapidjson::Document uMakefile;
std::ofstream makefile;

using namespace rapidjson;
using namespace std;

unsigned char customLinker = 0;                       /*If 1, umakefile has defined a custom linker*/
unsigned char selectiveCheckout = CHECKOUT_TYPE_FAST; /*Default to fast checkout as selective is VEEERRRRRYYYYY slow!*/

/*Allow for overriding in-built targets*/
bool hasCustomTargetAll = 0;
bool hasCustomTargetProgram = 0;
bool hasCustomTargetReset = 0;
bool hasCustomTargetChipErase = 0;

#define PWD(a)             \
    cout << a << " pwd: "; \
    fflush(stdout);        \
    system("pwd");         \
    cout << endl           \
         << endl

void processBook(string libName, string bookName)
{
    rapidjson::Document book;
    string tmpString;

    const string strFileName = "fileName";
    const string strLanguage = "language";

    string fileName;
    string language;

    /*Get book definition*/

    if (CHECKOUT_TYPE_SELECTIVE == selectiveCheckout)
    {
        /**** Selective checkout ****/
        chdir(libName.c_str());

        string clone;
        clone.append("git checkout master -- ");
        clone.append(bookName);
        clone.append("/");

        int sysRet = system(clone.c_str());
        if (0 != sysRet) /*If we have already cloned the repo... */
            cout << "Warning: Uanable to check out book: " << bookName << endl
                 << endl;

        chdir("../");

        if (0 == bookName.compare("uC"))
            return;
        /********************/
    }

    /*Generate book descriptor filename*/
    string fn = "./umake/";
    fn.append(libName.c_str());
    fn.append("/");
    fn.append(bookName);
    fn.append("/");
    fn.append(bookName);
    fn.append(".json");

    chdir("..");

    ifstream ifs(fn);
    IStreamWrapper isw(ifs);
    book.ParseStream(isw);

    if (book.HasParseError())
    {
        fprintf(stderr, "\nError(%s: %u): %s\n",
                fn.c_str(),
                (unsigned)book.GetErrorOffset(),
                GetParseError_En(book.GetParseError()));
        exit(1);
    }

    if (!book.HasMember("book"))
    {
        cout << "Error " << fn << " is missing file field\n";
        exit(1);
    }

    /********************/
    if (!book.HasMember("book"))
    {
        cout << "Error " << fn << " is missing book field\n";
        exit(1);
    }
    tmpString = book["book"].GetString();
    if (0 != tmpString.compare(bookName))
    {
        cout << "Error " << fn << " incorrect book defined.\n";
        exit(1);
    }

    if (!book.HasMember("files"))
    {
        chdir("umake");
        return;
    }
    const rapidjson::Value &files = book["files"];
    makefile << "# " << bookName << " include path" << endl;
    makefile << "INCLUDES += -I "
             << "./umake/" << libName << "/" << bookName << "/" << endl;
    makefile << "# " << bookName << " source files" << endl;
    /*Iterate through files array*/
    for (rapidjson::Value::ConstValueIterator itr = files.Begin(); itr != files.End(); ++itr)
    {
        const rapidjson::Value &file = *itr;
        assert(file.IsObject()); // each attribute is an object
        /*Iterate through each individual file object*/
        for (rapidjson::Value::ConstMemberIterator itr2 = file.MemberBegin(); itr2 != file.MemberEnd(); ++itr2)
        {
            /*Store fileName and language*/
            if (0 == strFileName.compare(itr2->name.GetString()))
                fileName = itr2->value.GetString();
            if (0 == strLanguage.compare(itr2->name.GetString()))
                language = itr2->value.GetString();
        }

        /*output correct SRCS line to makefile*/
        if (0 == language.compare("c"))
            makefile << "SRCS += ";
        else if (0 == language.compare("c++"))
            makefile << "CPPSRCS += ";
        else
        {
            cout << "Error undefined language in book: " << bookName << endl;
            exit(1);
        }
        makefile << "./umake/" << libName << "/" << bookName << "/";
        makefile << fileName << endl;
    }

    if (book.HasMember("cflags"))
    {
        makefile << "# " << bookName << " cflags\n";
        /*Iterate through defines array*/
        const Value &cflags = book["cflags"];
        assert(cflags.IsArray());
        for (SizeType i = 0; i < cflags.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "CFLAGS += " << cflags[i].GetString() << endl;
        }
    }

    if (book.HasMember("ldflags"))
    {
        makefile << "# " << bookName << " ldflags\n";
        assert(book.HasMember("ldflags"));
        /*Iterate through defines array*/
        const Value &ldflags = book["ldflags"];
        assert(ldflags.IsArray());
        for (SizeType i = 0; i < ldflags.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "LDFLAGS += " << ldflags[i].GetString() << endl;
        }
    }

    chdir("umake"); /*reset our PWD so that processLibs can continue*/
}

void processLibs(void)
{
    const string strLibPath = "libPath";
    const string strLibName = "libName";

    string libName;
    string libPath;

    if (uMakefile.HasMember("libraries"))
    {
        rapidjson::Value::MemberIterator attributeIterator = uMakefile.FindMember("libraries");
        const rapidjson::Value &libraries = uMakefile["libraries"];
        assert(libraries.IsArray()); // attributes is an array

        /*Change to lib directory*/
        chdir("umake");
        /*Iterate through libraries array*/
        for (rapidjson::Value::ConstValueIterator itr = libraries.Begin(); itr != libraries.End(); ++itr)
        {
            const rapidjson::Value &library = *itr;
            assert(library.IsObject()); // each attribute is an object
            /*Iterate through each individual library object*/
            for (rapidjson::Value::ConstMemberIterator itr2 = library.MemberBegin(); itr2 != library.MemberEnd(); ++itr2)
            {
                /*Store libName and libPath*/
                if (0 == strLibName.compare(itr2->name.GetString()))
                    libName = itr2->value.GetString();
                if (0 == strLibPath.compare(itr2->name.GetString()))
                    libPath = itr2->value.GetString();
            }
            // cout << endl
            //      << "libName: " << libName << endl
            //      << "libPath: " << libPath << endl;

            string clone;

            if (CHECKOUT_TYPE_SELECTIVE == selectiveCheckout)
            {
                /***** Selective clone **********/
                clone.append("git clone --depth 1 --quiet --no-checkout --filter=blob:none ");
                clone.append(libPath);
            }
            /**************/
            else
            {
                /**** Fast clone ****/
                clone.append("git clone --depth 1 ");
                clone.append(libPath);
                /**********/
            }
            int sysRet = system(clone.c_str());
            if (0 != sysRet) /*If we have already cloned the repo... */
            {
                clone.clear();
                clone.append(libName);
                chdir(clone.c_str());
                sysRet = system("git pull");
                /*Change back*/
                chdir("..");
            }

            /*Process checkout and branch*/
            if (library.HasMember("checkout"))
            {
                chdir(libName.c_str());
                clone.clear();
                clone.append("git checkout ");
                clone.append(library["checkout"].GetString());
                cout << clone << endl;
                system(clone.c_str());
                chdir("..");
            }
            if (library.HasMember("branch"))
            {
                chdir(libName.c_str());
                clone.clear();
                clone.append("git checkout ");
                clone.append(library["branch"].GetString());
                cout << clone << endl;
                system(clone.c_str());
                chdir("..");
            }
            /*Process books for this library*/
            if (library.HasMember("books"))
            {
                makefile << "# " << libName << ": Books" << endl;
                assert(library.HasMember("books"));
                /*Iterate through defines array*/
                const Value &books = library["books"];
                assert(books.IsArray());
                for (SizeType i = 0; i < books.Size(); i++) // Uses SizeType instead of size_t
                    processBook(libName, books[i].GetString());
                makefile << endl;
            }
            if (CHECKOUT_TYPE_SELECTIVE == selectiveCheckout)
            {
                /*If we are doing selective clone then we must explicitly checkout for the uC book as well*/
                processBook(libName, "uC");
            }
        }

        /*Change back*/
        chdir("..");
    }
    else
    {
        cout << "Error. No libraries defined." << endl;
        exit(1);
    }
}

void parseUmakefile(void)
{

    if (uMakefile.HasMember("buildDir"))
    {
        makefile << "# build directory\n";
        makefile << "BUILD = " << uMakefile["buildDir"].GetString() << "\n";
    }
    else
    {
        cout << "Error. buildDir required in umakefile." << endl;
        exit(1);
    }

    if (uMakefile.HasMember("target"))
    {
        makefile << "# target binary name\n";
        makefile << "BIN = " << uMakefile["target"].GetString() << "\n\n";
    }
    else
    {
        cout << "Error. target required in umakefile." << endl;
        exit(1);
    }

    if (uMakefile.HasMember("linkerFile"))
    {
        assert(uMakefile.HasMember("linkerFile"));
        makefile << "# custom linkerfile\n";
        customLinker = 1;
        makefile << "LDFLAGS += -Wl,--script=" << uMakefile["linkerFile"].GetString() << "\n";
    }

    if (!uMakefile.HasMember("microcontroller"))
    {
        cout << "Error. microcontroller required in umakefile." << endl;
        exit(1);
    }

    if (!uMakefile.HasMember("toolchain"))
    {
        cout << "Error. toolchain required in umakefile." << endl;
        exit(1);
    }

    makefile << "# Project sources\n";
    if (uMakefile.HasMember("c_sources"))
    {
        makefile << "# C sources\n";
        assert(uMakefile.HasMember("c_sources"));
        /*Iterate through defines array*/
        const Value &sources = uMakefile["c_sources"];
        assert(sources.IsArray());
        for (SizeType i = 0; i < sources.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "SRCS += " << sources[i].GetString() << endl;
        }
        makefile << endl;
    }

    if (uMakefile.HasMember("cpp_sources"))
    {
        makefile << "# CPP sources\n";
        assert(uMakefile.HasMember("cpp_sources"));
        /*Iterate through defines array*/
        const Value &sources = uMakefile["cpp_sources"];
        assert(sources.IsArray());
        for (SizeType i = 0; i < sources.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "CPPSRCS += " << sources[i].GetString() << endl;
        }
        makefile << endl;
    }

    if (uMakefile.HasMember("includes"))
    {
        makefile << "# Project include directories\n";
        assert(uMakefile.HasMember("includes"));
        /*Iterate through defines array*/
        const Value &includes = uMakefile["includes"];
        assert(includes.IsArray());
        for (SizeType i = 0; i < includes.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "INCLUDES += -I " << includes[i].GetString() << endl;
        }
        makefile << endl;
    }

    if (uMakefile.HasMember("defines"))
    {
        makefile << "# Project defines\n";
        assert(uMakefile.HasMember("defines"));
        /*Iterate through defines array*/
        const Value &includes = uMakefile["defines"];
        assert(includes.IsArray());
        for (SizeType i = 0; i < includes.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "DEFINES += -D " << includes[i].GetString() << endl;
        }
        makefile << endl;
    }

    if (uMakefile.HasMember("cflags"))
    {
        makefile << "# Project cflags\n";
        /*Iterate through defines array*/
        const Value &cflags = uMakefile["cflags"];
        assert(cflags.IsArray());
        for (SizeType i = 0; i < cflags.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "CFLAGS += " << cflags[i].GetString() << endl;
        }
        makefile << endl;
    }

    if (uMakefile.HasMember("ldflags"))
    {
        makefile << "# Project ldflags\n";
        assert(uMakefile.HasMember("ldflags"));
        /*Iterate through defines array*/
        const Value &ldflags = uMakefile["ldflags"];
        assert(ldflags.IsArray());
        for (SizeType i = 0; i < ldflags.Size(); i++) // Uses SizeType instead of size_t
        {
            makefile << "LDFLAGS += " << ldflags[i].GetString() << endl;
        }
        makefile << endl;
    }
}

int main(int argc, char *argv[])
{
    string line, text;

    /*Deal with umake clean*/
    if (argc > 1)
        if (0 == strncmp(argv[1], "clean", 5))
        {
            system("make clean");
            system("rm -rf ./umake");
            system("rm -f Makefile");
            exit(0);
        }

    /*Input source file*/
    ifstream in("umakefile");

    /*output Makefile*/
    makefile.open("Makefile");

    /*Create umake dir if it doesn't exist*/
    if (mkdir("umake", 0700) != 0 && errno != EEXIST)
        cout << "Error: " << errno << endl;

    /*Get umakefile*/
    ifstream ifs("umakefile");
    IStreamWrapper isw(ifs);
    uMakefile.ParseStream(isw);
    /********************/

    if (CHECKOUT_TYPE_SELECTIVE == selectiveCheckout)
        cout << "Selective checkout enabled, this may take a while!" << endl
             << endl;

    /*Process libraries*/
    processLibs();

    makefile << ".PHONY: all directory clean size\n\n";

    parseUmakefile();
    parseMicrocontroller(uMakefile, makefile, customLinker);

    /*Generate bulk of Makefile
    * Order of function calls here matters!
    */
    generateToolchainArm_none_eabi(makefile);

    processTargets(uMakefile, makefile);

    if (!hasCustomTargetAll)
        generateTargetAll(makefile);
    if (!hasCustomTargetProgram)
        generateTargetProgram(makefile);
    if (!hasCustomTargetReset)
        generateTargetReset(makefile);
    if (!hasCustomTargetChipErase)
        generateTargetChipErase(makefile);
    generateBoilerPlate(makefile);

    makefile.close();
    return 0;
}