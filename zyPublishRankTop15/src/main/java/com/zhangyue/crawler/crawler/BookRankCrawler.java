package com.zhangyue.crawler.crawler;

import com.zhangyue.crawler.entity.Book;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class BookRankCrawler {
    private static final String USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1";
    private static final int TIMEOUT = 10000;

    public List<Book> crawlRankList(String rankUrl, int topN) throws IOException {
        List<Book> books = new ArrayList<>();
        Document doc = Jsoup.connect(rankUrl)
                .userAgent(USER_AGENT)
                .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                .header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
                .header("Accept-Encoding", "gzip, deflate, br")
                .header("Connection", "keep-alive")
                .header("Upgrade-Insecure-Requests", "1")
                .timeout(TIMEOUT)
                .get();

        Elements bookItems = doc.select("ul.rank_booklist li");
        int count = 0;
        for (Element item : bookItems) {
            if (count >= topN) break;

            try {
                Element linkElement = item.selectFirst("a[data-js=rankBook]");
                if (linkElement == null) continue;

                String detailUrl = linkElement.attr("href");
                String title = item.selectFirst("dt").text();
                String author = item.selectFirst("dd.author").text();

                BookDetail detail = getBookDetail(detailUrl);

                Book book = new Book();
                book.setRank(++count);
                book.setTitle(title);
                book.setAuthor(author);
                book.setCategory(detail.category);
                book.setRating(detail.rating);

                books.add(book);
                System.out.println("已抓取: " + count + ". " + title);

                Thread.sleep(500);
            } catch (Exception e) {
                System.err.println("抓取书籍失败: " + e.getMessage());
            }
        }
        return books;
    }

    private BookDetail getBookDetail(String detailUrl) throws IOException {
        BookDetail detail = new BookDetail();
        try {
            Document doc = Jsoup.connect(detailUrl)
                    .userAgent(USER_AGENT)
                    .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                    .header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
                    .header("Accept-Encoding", "gzip, deflate, br")
                    .header("Connection", "keep-alive")
                    .header("Upgrade-Insecure-Requests", "1")
                    .timeout(TIMEOUT)
                    .get();

            Element scoreElement = doc.selectFirst("div.score");
            if (scoreElement != null) {
                String scoreText = scoreElement.text();
                detail.rating = parseRating(scoreText);
            }

            Element categoryElement = doc.selectFirst("dd.tagbtn span[data-js=goCategory]");
            if (categoryElement != null) {
                detail.category = categoryElement.text();
            } else {
                Element tagElement = doc.selectFirst("dd span.tag");
                if (tagElement != null) {
                    detail.category = tagElement.text();
                }
            }
        } catch (Exception e) {
            System.err.println("获取详情失败: " + detailUrl + ", " + e.getMessage());
        }
        return detail;
    }

    private double parseRating(String ratingText) {
        try {
            if (ratingText != null && ratingText.contains("分")) {
                return Double.parseDouble(ratingText.replace("分", "").trim());
            }
        } catch (NumberFormatException e) {
            return 0.0;
        }
        return 0.0;
    }

    private static class BookDetail {
        String category = "未知";
        double rating = 0.0;
    }
}
