package com.example.finalproject;

public class Post {
    private final String title;
    private final String text;
    private final String createdDate;
    private final String imageUrl;
    private final String confidence;
    private final String bbox;

    public Post(String title, String text, String createdDate, String imageUrl, String confidence, String bbox) {
        this.title = title;
        this.text = text;
        this.createdDate = createdDate;
        this.confidence = confidence;
        this.bbox = bbox;

        // [CRITICAL CHANGE]
        // If the server sends "127.0.0.1", KEEP IT.
        // We are now using ADB Reverse, so "127.0.0.1" inside the emulator IS valid.
        this.imageUrl = imageUrl;
    }

    public String getTitle() { return title; }
    public String getText() { return text; }
    public String getCreatedDate() { return createdDate; }
    public String getImageUrl() { return imageUrl; }
    public String getConfidence() { return confidence; }
    public String getBbox() { return bbox; }
}