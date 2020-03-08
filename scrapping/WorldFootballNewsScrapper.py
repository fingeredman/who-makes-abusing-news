from bs4 import BeautifulSoup
from datetime import datetime as dt
from datetime import timedelta as td
import requests
import pickle
import urllib
import random
import time
import json
import re

import configure as con

class WorldFootballNewsScrapper():
    def __init__(self):
        self.file_name = con.FILE_NAME
                  
    def scrapping(self, date, limit=-1):
        article_dict_list = []
        article_id_list = self.__get_article_id(date)
        for article_id_dict in article_id_list[:limit]:
            try:
                aid = article_id_dict["aid"]
                oid = article_id_dict["oid"]
                article_dict = self.__get_article(oid, aid)
                comment_list = self.__get_comment_list(oid, aid)
                article_dict["comment_list"] = comment_list
                for comment in comment_list:
                    comment_number = comment["comment_number"]
                    reply_list = self.__get_reply_list(oid, aid, comment_number)
                    comment["reply_list"] = reply_list
                article_dict["comment_list"] = comment_list
                article_dict_list.append(article_dict)
            except:
                #print(aid, oid)
                None
        self.__save(self.file_name + date, article_dict_list)
        return article_dict_list
    
    def load(self, file_name):
        with open(file_name, "rb") as f:
            data = pickle.load(f)
        return data
    
    def __save(self, file_name, data):
        with open(file_name, "wb") as f:
            pickle.dump(data, f, -1)
        print("Saved. ", file_name)
    
    def __get_some_rest(self):
        time.sleep(random.randint(1, 100)/10)

    def __get_user_agent(self):
        user_agent_list = open(con.USER_AGENT_PATH, encoding="utf-8").read().split("\n")
        return random.choice(user_agent_list)

    def __get_article_id(self, date):
        world_sports_tag = "wfootball"
        max_page = 100
        page_size = 20
        article_id_list = []
        for page in range(1, max_page+1):
            newspage_url = "https://sports.news.naver.com/" + world_sports_tag 
            newspage_url += "/news/list.nhn?date=" + date
            newspage_url += "&isphoto=N&page=" + str(page)
            headers = {'User-Agent': self.__get_user_agent(), "referer": newspage_url}
            r = requests.get(newspage_url, headers=headers)
            article_list = json.loads(r.text)["list"]
            article_count = len(article_list)
            for article in article_list:
                aid = article["aid"]
                oid = article["oid"]
                press_name = article["officeName"]
                view_count = article["totalCount"]
                sub_content = article["subContent"]
                section_name = article["sectionName"]
                article_id_dice = {
                    "aid": aid,
                    "oid": oid,
                    "press_name": press_name,
                    "view_count": view_count,
                    "sub_content": sub_content,
                    "section_name": section_name
                }
                article_id_list.append(article_id_dice)
            if article_count != page_size:
                break
        return article_id_list

    def __get_article(self, oid, aid):
        article_url = "https://sports.news.naver.com/news.nhn?oid=" + oid + "&aid=" + aid
        page = urllib.request.urlopen(article_url)
        soup = BeautifulSoup(page, "html.parser")
        press_name = soup.find('span', {'class':'logo',}).find("img").attrs["alt"]
        press_url = soup.find('span', {'class':'logo',}).find("a").attrs["href"]#
        title = soup.find('div', {'class':'news_headline',}).find('h4', {'class':'title',}).text
        created_str = soup.find('div', {'class':'news_headline',}).find('div', {'class':'info',}).findAll("span")[0].text[5:]
        created_datetime = created_str[:11] + created_str[14:]
        created_ampm = created_str[12:14]
        created = dt.strptime(created_datetime, '%Y.%m.%d. %H:%M')
        if created_ampm == "오후":
            created + td(hours=12)
        updated_str = soup.find('div', {'class':'news_headline',}).find('div', {'class':'info',}).findAll("span")[1].text[5:]
        updated_datetime = updated_str[:11] + updated_str[14:]
        updated_ampm = updated_str[12:14]
        updated = dt.strptime(updated_datetime, '%Y.%m.%d. %H:%M')
        if updated_ampm == "오후":
            updated + td(hours=12)
        org_url = soup.find('div', {'class':'news_headline',}).find('div', {'class':'info',}).find("a").attrs["href"]
        content = soup.find('div', {'class':'news_end',}).text.strip()
        aid_regex = r"aid=(\w+)"
        aid_pattern = re.compile(aid_regex)
        aid = aid_pattern.findall(article_url)[0]
        oid_regex = r"oid=(\w+)"
        oid_pattern = re.compile(oid_regex)
        oid = oid_pattern.findall(article_url)[0]
        scrapped = dt.now()
        article_dict = {
            "press_name": press_name,
            "press_url": press_url,
            "title": title,
            "created": created,
            "updated": updated,
            "org_url": org_url,
            "url": article_url,
            "content": content,
            "aid": aid,
            "oid": oid,
            "scrapped": scrapped
        }
        return article_dict

    def __get_comment_list(self, oid, aid):
        page_size = 100
        max_page = 100
        comment_dict_list = []
        for page in range(1, max_page+1):
            comment_url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?"
            comment_url += "ticket=sports&templateId=view&pool=cbox2&_callback=jQuery111303496352025980869_1574864079631"
            comment_url += "&lang=ko&country=KR&objectId=news" + oid + "%2C" + aid
            comment_url += "&categoryId=&pageSize=" + str(page_size)
            comment_url += "&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=" + str(page)
            comment_url += "&initialize=true&userType=&useAltSort=true&replyPageSize=20&moveTo=&sort=LIKE&_=1574864079632"
            headers = {'User-Agent': self.__get_user_agent(), "referer": comment_url}
            r = requests.get(comment_url, headers=headers)
            query_regex = r"jQuery[\d_]*\((.*)\)"
            query_pattern = re.compile(query_regex)
            query = query_pattern.findall(r.text)[0]
            query_dict = json.loads(query)
            comment_list = query_dict["result"]["commentList"]
            comment_count = len(comment_list)
            for comment in comment_list:
                comment_number = comment["commentNo"]
                parent_comment_number = comment["parentCommentNo"]
                reply_count = comment["replyCount"]
                comment_content = comment["contents"]
                user_name = comment["userName"]
                masked_user_name = comment["maskedUserName"]
                created_gmt = comment["regTime"][:19]
                created = dt.strptime(created_gmt, '%Y-%m-%dT%H:%M:%S')
                updated_gmt = comment["modTime"][:19]
                updated = dt.strptime(updated_gmt, '%Y-%m-%dT%H:%M:%S')
                sympathy_count = comment["sympathyCount"]
                antipathy_count = comment["antipathyCount"]
                user_id = comment["maskedUserId"]
                scrapped = dt.now()
                comment_dict = {
                    "comment_number": comment_number,
                    "parent_comment_number": parent_comment_number,
                    "reply_count": reply_count,
                    "comment_content": comment_content,
                    "user_name": user_name,
                    "masked_user_name": masked_user_name,
                    "created": created,
                    "updated": updated,
                    "sympathy_count": sympathy_count,
                    "antipathy_count": antipathy_count,
                    "user_id": user_id,
                    "scrapped": scrapped
                }
                comment_dict_list.append(comment_dict)
            if comment_count != page_size:
                break
        return comment_dict_list

    def __get_reply_list(self, oid, aid, comment_number):
        page_size = 100
        max_page = 100
        reply_dict_list = []
        for page in range(1, max_page+1):
            reply_url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=sports"
            reply_url += "&templateId=view&pool=cbox2&_callback=jQuery111309335768450595043_1574868846064&lang=ko"
            reply_url += "&country=KR&objectId=news" + oid + "%2C" + aid
            reply_url += "&categoryId=&pageSize=" + str(page_size)
            reply_url += "&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo=" + str(comment_number)
            reply_url += "&page=" + str(page)
            reply_url += "&userType=&moreType=next&_=1574868846066"
            headers = {'User-Agent': self.__get_user_agent(), "referer": reply_url}
            r = requests.get(reply_url, headers=headers)
            query_regex = r"jQuery[\d_]*\((.*)\)"
            query_pattern = re.compile(query_regex)
            query = query_pattern.findall(r.text)[0]
            query_dict = json.loads(query)
            reply_list = query_dict["result"]["commentList"]
            reply_count = len(reply_list)
            for reply in reply_list:
                comment_number = reply["commentNo"]
                parent_comment_number = reply["parentCommentNo"]
                reply_count = reply["replyCount"]
                comment_content = reply["contents"]
                user_name = reply["userName"]
                masked_user_name = reply["maskedUserName"]
                created_gmt = reply["regTime"][:19]
                created = dt.strptime(created_gmt, '%Y-%m-%dT%H:%M:%S')
                updated_gmt = reply["regTime"][:19]
                updated = dt.strptime(updated_gmt, '%Y-%m-%dT%H:%M:%S')
                sympathy_count = reply["sympathyCount"]
                antipathy_count = reply["antipathyCount"]
                user_id = reply["maskedUserId"]
                scrapped = dt.now()
                reply_dict = {
                    "comment_number": comment_number,
                    "parent_comment_number": parent_comment_number,
                    "reply_count": reply_count,
                    "comment_content": comment_content,
                    "user_name": user_name,
                    "masked_user_name": masked_user_name,
                    "created": created,
                    "updated": updated,
                    "sympathy_count": sympathy_count,
                    "antipathy_count": antipathy_count,
                    "user_id": user_id,
                    "scrapped": scrapped
                }
                reply_dict_list.append(reply_dict)
            if reply_count != page_size:
                break
        return reply_dict_list