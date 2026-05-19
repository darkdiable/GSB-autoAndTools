package com.zhangyue.crawler.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.zhangyue.crawler.entity.Book;

import java.io.File;
import java.io.IOException;
import java.util.List;

public class JsonFileWriter {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    static {
        objectMapper.enable(SerializationFeature.INDENT_OUTPUT);
    }

    public static void writeBooksToJson(List<Book> books, String filePath) throws IOException {
        File file = new File(filePath);
        File parentDir = file.getParentFile();
        if (parentDir != null && !parentDir.exists()) {
            parentDir.mkdirs();
        }
        objectMapper.writeValue(file, books);
        System.out.println("JSON文件已生成: " + filePath);
    }
}
