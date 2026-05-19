package com.zhangyue.crawler.entity;

public class Book {
    private int rank;
    private String title;
    private String author;
    private String category;
    private double rating;

    public Book() {
    }

    public Book(int rank, String title, String author, String category, double rating) {
        this.rank = rank;
        this.title = title;
        this.author = author;
        this.category = category;
        this.rating = rating;
    }

    public int getRank() {
        return rank;
    }

    public void setRank(int rank) {
        this.rank = rank;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public double getRating() {
        return rating;
    }

    public void setRating(double rating) {
        this.rating = rating;
    }

    @Override
    public String toString() {
        return "Book{" +
                "rank=" + rank +
                ", title='" + title + '\'' +
                ", author='" + author + '\'' +
                ", category='" + category + '\'' +
                ", rating=" + rating +
                '}';
    }
}
