import scrapy
from scrapy.spiders import CrawlSpider,Rule
from scrapy.linkextractors import LinkExtractor


class LigueSpider(CrawlSpider):
    name = "ligue"
    allowed_domains = ["www.ligue1.fr"]
    start_urls = [f"https://www.ligue1.fr/calendrier-resultats?seasonId=20{i}-20{i+1}" for i in range(14,24)]

    rules = (
        Rule(LinkExtractor(allow="matchDay"),callback="parse_score"),
    )

    def parse_score(self, response):
        home = response.css("div.club.home").css(".calendarTeamNameDesktop::text").getall()
        matchids = [i.split("_")[0] for i in response.css("li::attr(id)").getall()]
        homeScores = [response.css(f"span#{id}_homeScore::text").get() for id in matchids]
        awayScores = [response.css(f"span#{id}_awayScore::text").get() for id in matchids]
        away = res = response.css("div.club.away").css(".calendarTeamNameDesktop::text").getall()
        for idx,id in enumerate(matchids) :
            yield {
                'id' : id,
                'homeTeam' : home[idx],
                'homeScore' : homeScores[idx],
                'awayTeam'  : away[idx],
                'awayScore' : awayScores[idx],
                'season'    : response.url.split("&")[0].split('seasonId=')[-1],
                'matchDay'  : response.url.split("matchDay=")[-1].split("&")[0]
            } 