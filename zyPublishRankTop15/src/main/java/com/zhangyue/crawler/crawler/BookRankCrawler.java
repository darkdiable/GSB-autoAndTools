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
    private static final String[] USER_AGENTS = {
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
    };
    private static final int TIMEOUT = 10000;

    public List<Book> crawlRankList(String rankUrl, int topN) throws IOException, InterruptedException {
        List<Book> books = new ArrayList<>();
        int retryCount = 0;
        int maxRetries = 3;
        Document doc = null;

        while (retryCount < maxRetries && doc == null) {
            try {
                String currentUserAgent = USER_AGENTS[retryCount % USER_AGENTS.length];
                doc = Jsoup.connect(rankUrl)
                        .userAgent(currentUserAgent)
                        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
                        .header("Accept-Language", "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2")
                        .header("Accept-Encoding", "gzip, deflate, br")
                        .header("Connection", "keep-alive")
                        .header("Upgrade-Insecure-Requests", "1")
                        .header("Sec-Fetch-Dest", "document")
                        .header("Sec-Fetch-Mode", "navigate")
                        .header("Sec-Fetch-Site", "none")
                        .header("Sec-Fetch-User", "?1")
                        .header("Pragma", "no-cache")
                        .header("Cache-Control", "no-cache")
                        .ignoreHttpErrors(true)
                        .timeout(TIMEOUT)
                        .get();

                if (isCaptchaPage(doc)) {
                    doc = null;
                    retryCount++;
                    if (retryCount < maxRetries) {
                        Thread.sleep(5000 * retryCount);
                    }
                }
            } catch (IOException e) {
                retryCount++;
                if (retryCount < maxRetries) {
                    Thread.sleep(5000 * retryCount);
                } else {
                    throw e;
                }
            }
        }

        if (doc == null) {
            throw new IOException("无法获取页面内容，可能遇到了验证码");
        }

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

    private BookDetail getBookDetail(String detailUrl) throws IOException, InterruptedException {
        BookDetail detail = new BookDetail();
        int retryCount = 0;
        int maxRetries = 2;
        Document doc = null;

        while (retryCount < maxRetries && doc == null) {
            try {
                String currentUserAgent = USER_AGENTS[retryCount % USER_AGENTS.length];
                doc = Jsoup.connect(detailUrl)
                        .userAgent(currentUserAgent)
                        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
                        .header("Accept-Language", "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2")
                        .header("Accept-Encoding", "gzip, deflate, br")
                        .header("Connection", "keep-alive")
                        .header("Upgrade-Insecure-Requests", "1")
                        .header("Sec-Fetch-Dest", "document")
                        .header("Sec-Fetch-Mode", "navigate")
                        .header("Sec-Fetch-Site", "same-origin")
                        .header("Referer", "https://m.zhangyue.com/rank/")
                        .header("Pragma", "no-cache")
                        .header("Cache-Control", "no-cache")
                        .ignoreHttpErrors(true)
                        .timeout(TIMEOUT)
                        .get();

                if (isCaptchaPage(doc)) {
                    doc = null;
                    retryCount++;
                    if (retryCount < maxRetries) {
                        Thread.sleep(3000 * retryCount);
                    }
                }
            } catch (IOException e) {
                retryCount++;
                if (retryCount < maxRetries) {
                    Thread.sleep(3000 * retryCount);
                } else {
                    return detail;
                }
            }
        }

        if (doc == null) {
            return detail;
        }

        Element scoreElement = doc.selectFirst("dl.main span.yellow");
        if (scoreElement != null) {
            String scoreText = scoreElement.text();
            detail.rating = parseRating(scoreText);
        }
        if (detail.rating == 0.0) {
            Element altScoreElement = doc.selectFirst("div.cover span.yellow");
            if (altScoreElement != null) {
                detail.rating = parseRating(altScoreElement.text());
            }
        }
        if (detail.rating == 0.0) {
            Element scoreInDl = doc.selectFirst("dl.main dd:has(span.stars) span.yellow");
            if (scoreInDl != null) {
                detail.rating = parseRating(scoreInDl.text());
            }
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
        return detail;
    }

    private boolean isCaptchaPage(Document doc) {
        String html = doc.html();
        String title = doc.title();
        return html.contains("captcha") || html.contains("TCaptcha") || html.contains("验证码") ||
               html.contains("安全验证") || title.contains("验证码") || title.contains("WAF") ||
               title.contains("拦截") || html.contains("WAF") || html.contains("blocked") ||
               html.length() < 3000;
    }

    private double parseRating(String ratingText) {
        try {
            if (ratingText != null && !ratingText.isEmpty()) {
                String text = ratingText.trim();
                if (text.contains("分")) {
                    text = text.replace("分", "").trim();
                }
                return Double.parseDouble(text);
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
