#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

# this script suggests a country to invest in based on CAPE and momentum
# first it finds the country using data from starcapital.de
# then it checks if there is a heavy enough weighted ETF for that country, and if not, finds next country
# finally the script can email the results to interested addressee

import sys
import json
import requests
from bs4 import BeautifulSoup


starcapital_url = "https://www.starcapital.de/fileadmin/charts/Res_Aktienmarktbewertungen_FundamentalKZ_Tbl.php?lang=en"
etfdb_url = "http://etfdb.com/country/"


def get_json():
    response = requests.get(starcapital_url)
    parsed_json = json.loads(response.content)
    return parsed_json


def get_countries(parsed_json, number_of_countries):
    country_list = parsed_json['rows']
    curated_list = []

    for c in country_list:
        if c['c'][2]['v'] is not None and c['c'][10]['v'] is not None:
            curated_list.append(c)

    curated_list.sort(key=lambda x: x['c'][2]['v'])
    top10 = []
    for i in range(0, 10):
        top10.append(curated_list[i])
    top10.sort(key=lambda x: (x['c'][9]['v'], x['c'][8]['v']), reverse=True)

    countries = []
    for i in range(0,number_of_countries):
        countries.append(top10[0+i]['c'][0]['v'])
    return countries


def get_etf(lookup_country):
    result = requests.get(etfdb_url + lookup_country)
    if result.status_code == 404:
        return ""
    soup = BeautifulSoup(result.content.decode('utf-8'), 'html5lib')
    weighting = soup.find("td", {"data-th": "Weighting"})
    weighting = float(weighting.text.strip(' \t\n\r%'))
    minimum_weighting = 50.0
    if weighting > minimum_weighting:
        ticker = soup.find("td", {"data-th": "Ticker"})
        return ticker.text
    else:
        return ""


def send_email(subject, email_body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    fromaddr = sys.argv[1]
    toaddr = sys.argv[3]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, sys.argv[2])
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


if __name__ == '__main__':
    try:
        json = get_json()
        etf = ""
        countries = get_countries(json, 5)
        print(countries)
        for country in countries:
            etf = get_etf(country)
            if etf != "":
                break

        if len(sys.argv) == 2 and sys.argv[1] == "cli":
            if etf == "":
                print("No ETF found!")
            else:
                print("Found an ETF: " + etf + ". Topp 5 länder: " + str(countries))
        elif len(sys.argv) != 4:
            print("No command line arguments supplied. (Looking for: From Email, From Email Password, To Email)")
        else:
            message = etf +  ". Topp 5 länder: " + str(countries)
            send_email("Kvartalets ETF!", etf)
    except LookupError as le:
        if len(sys.argv) != 4:
            print(le.message)
        else:
            send_email("Lookup error", le.message)
