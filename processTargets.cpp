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
    const string strTargetName = "targetName";
    const string strTargetContent = "content";

    if (uMakefile.HasMember("targets"))
    {
        rapidjson::Value::MemberIterator attributeIterator = uMakefile.FindMember("targets");
        const rapidjson::Value &targets = uMakefile["targets"];
        assert(targets.IsArray()); // attributes is an array

        /*Iterate through targets array*/
        for (rapidjson::Value::ConstValueIterator itr = targets.Begin(); itr != targets.End(); ++itr)
        {
            const rapidjson::Value &target = *itr;
            assert(target.IsObject()); // each attribute is an object
            /*Iterate through each individual library object*/
            for (rapidjson::Value::ConstMemberIterator itr2 = target.MemberBegin(); itr2 != target.MemberEnd(); ++itr2)
            {
                if (0 == strTargetName.compare(itr2->name.GetString())) /*Output target name*/
                {
                    /*Check to see if the target overrides one of the default targets*/
                    if (0 == std::string("program").compare(itr2->value.GetString()))
                        hasCustomTargetProgram = 1;
                    makefile << "# custom targets" << endl;
                    makefile << itr2->value.GetString() << ":\n";
                }
                else if (0 == strTargetContent.compare(itr2->name.GetString())) /*Output target contents*/
                {
                    /*Iterate through content array*/
                    const Value &targetContent = target["content"];
                    assert(targetContent.IsArray());
                    for (SizeType i = 0; i < targetContent.Size(); i++) // Uses SizeType instead of size_t
                    {
                        makefile << "\t" << targetContent[i].GetString() << "\n";
                    }
                    makefile << endl;
                }
                else
                {
                    /* code */
                }
            }
        }
    }
    else
    {
        cout << "Error. No targets defined." << endl;
        exit(1);
    }
}