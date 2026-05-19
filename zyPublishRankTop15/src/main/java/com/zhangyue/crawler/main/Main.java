package com.zhangyue.crawler.main;

import com.zhangyue.crawler.crawler.BookRankCrawler;
import com.zhangyue.crawler.entity.Book;
import com.zhangyue.crawler.util.JsonFileWriter;

import java.util.List;

public class Main {
    private static final String BASE_URL = "https://m.zhangyue.com/rank/list/";
    private static final String EDITOR_RECOMMEND_URL = BASE_URL + "14374?name=%E4%B8%BB%E7%BC%96%E6%8E%A8%E8%8D%90%E6%A6%9C";
    private static final String BEST_SELLER_URL = BASE_URL + "19268?name=%E6%8E%8C%E9%98%85%E7%95%85%E9%94%80%E6%A6%9C";
    private static final String DISCOUNT_URL = BASE_URL + "18474?name=%E7%89%B9%E4%BB%B7%E6%8A%98%E6%89%A3%E6%A6%9C";
    private static final int TOP_N = 15;

    public static void main(String[] args) {
        BookRankCrawler crawler = new BookRankCrawler();
        String outputDir = System.getProperty("user.dir") + "/output/";

        try {
            System.out.println("========== 开始爬取主编推荐榜 ==========");
            List<Book> editorRecommendBooks = crawler.crawlRankList(EDITOR_RECOMMEND_URL, TOP_N);
            JsonFileWriter.writeBooksToJson(editorRecommendBooks, outputDir + "editor_recommend_top15.json");
            System.out.println("主编推荐榜爬取完成，共 " + editorRecommendBooks.size() + " 本书\n");

            Thread.sleep(2000);

            System.out.println("========== 开始爬取掌阅畅销榜 ==========");
            List<Book> bestSellerBooks = crawler.crawlRankList(BEST_SELLER_URL, TOP_N);
            JsonFileWriter.writeBooksToJson(bestSellerBooks, outputDir + "best_seller_top15.json");
            System.out.println("掌阅畅销榜爬取完成，共 " + bestSellerBooks.size() + " 本书\n");

            Thread.sleep(2000);

            System.out.println("========== 开始爬取特价折扣榜 ==========");
            List<Book> discountBooks = crawler.crawlRankList(DISCOUNT_URL, TOP_N);
            JsonFileWriter.writeBooksToJson(discountBooks, outputDir + "discount_top15.json");
            System.out.println("特价折扣榜爬取完成，共 " + discountBooks.size() + " 本书\n");

            System.out.println("========== 所有榜单爬取完成 ==========");
            System.out.println("JSON文件输出目录: " + outputDir);

        } catch (Exception e) {
            System.err.println("爬取过程中发生错误: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
