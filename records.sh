#! /bin/bash

read_dom()
{
    local IFS=\>
    read -d \< ENTITY CONTENT
}

curl --user admin:Ocs881212 -H "Content-Type: text/xml; charset=utf-8" -H "SOAPAction:"  -d @FindRecordings.xml -X POST http://10.70.66.16/onvif/search_service > find_rec.xml
token=""

while read_dom; do
    if [[ $ENTITY = "tse:SearchToken" ]]; then
        token="$CONTENT"
        echo "search token = $token"
    fi
done < find_rec.xml

request="<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s=\"http://www.w3.org/2003/05/soap-envelope\">
<s:Body xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\">
<GetRecordingSearchResults xmlns=\"http://www.onvif.org/ver10/search/wsdl\">
<SearchToken>$token</SearchToken>
<MinResults>1</MinResults>
<WaitTime>PT5S</WaitTime>
</GetRecordingSearchResults>
</s:Body>
</s:Envelope>"

echo "$request" > GetRecordingSearchResults.xml
sleep 1 # hacky tempo
curl --digest --user admin:Ocs881212 -H "Content-Type: text/xml; charset=utf-8" -H "SOAPAction:" -d @GetRecordingSearchResults.xml -X POST http://10.70.66.16/onvif/search_service