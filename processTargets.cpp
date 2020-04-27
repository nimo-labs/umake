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
#include <string>
#include <fstream>
#include <iostream>

#include "umake.h"
#include "processTargets.h"

using namespace rapidjson;
using namespace std;

void processTargets(rapidjson::Document &uMakefile, std::ofstream &makefile)
{
    string targetName;

    if (uMakefile.HasMember("targets"))
    {
        rapidjson::Value::MemberIterator attributeIterator = uMakefile.FindMember("targets");
        const rapidjson::Value &targets = uMakefile["targets"];
        assert(targets.IsArray()); // attributes is an array

        /*Iterate through targets array*/
        makefile << "# custom targets" << endl;
        for (rapidjson::Value::ConstValueIterator itr = targets.Begin(); itr != targets.End(); ++itr)
        {
            const rapidjson::Value &target = *itr;
            assert(target.IsObject()); // each attribute is an object
            /*Iterate through each individual library object*/
            for (rapidjson::Value::ConstMemberIterator itr2 = target.MemberBegin(); itr2 != target.MemberEnd(); ++itr2)
            {
                if (0 == string("targetName").compare(itr2->name.GetString())) /*Output target name*/
                {
                    /*Check to see if the target overrides one of the default targets*/
                    if (0 == string("all").compare(itr2->value.GetString()))
                    {
                        hasCustomTargetAll = 1;
                        targetName = "_all";
                    }
                    else
                    {
                        targetName = itr2->value.GetString();
                    }

                    if (0 == string("program").compare(itr2->value.GetString()))
                        hasCustomTargetProgram = 1;
                    if (0 == string("reset").compare(itr2->value.GetString()))
                        hasCustomTargetReset = 1;
                    if (0 == string("chip-erase").compare(itr2->value.GetString()))
                        hasCustomTargetChipErase = 1;

                    makefile << targetName << ": ";
                }

                if (0 == string("depends").compare(itr2->name.GetString())) /*Output target name*/
                {
                    makefile << itr2->value.GetString() << endl;
                }

                if (0 == string("content").compare(itr2->name.GetString())) /*Output target contents*/
                {
                    if (!target.HasMember("depends"))
                        makefile << endl;
                    /*Iterate through content array*/
                    const Value &targetContent = target["content"];
                    assert(targetContent.IsArray());
                    for (SizeType i = 0; i < targetContent.Size(); i++) // Uses SizeType instead of size_t
                    {
                        makefile << "\t" << targetContent[i].GetString() << "\n";
                    }
                    makefile << endl;
                }
            }
        }
    }
}