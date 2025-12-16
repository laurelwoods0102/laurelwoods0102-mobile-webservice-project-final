package com.example.finalproject;

import android.content.Context;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class FileUtils {

    // Unique temp file for each URL
    public static File getTempFile(Context context, String url) {
        String fileName = "temp_" + url.hashCode() + ".png";
        return new File(context.getCacheDir(), fileName);
    }

    // Downloads URL to a file and returns true ONLY if valid PNG
    public static boolean downloadFileSafely(String urlString, File targetFile) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(urlString);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(15000); // Longer timeout
            connection.setReadTimeout(15000);
            connection.setRequestProperty("Connection", "close"); // Avoid Keep-Alive issues
            connection.connect();

            if (connection.getResponseCode() != 200) return false;

            InputStream input = connection.getInputStream();
            FileOutputStream output = new FileOutputStream(targetFile);

            byte[] buffer = new byte[4096];
            int n;
            while ((n = input.read(buffer)) != -1) {
                output.write(buffer, 0, n);
            }
            output.close();
            input.close();

            return isPngValid(targetFile);

        } catch (Exception e) {
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    // Checks for PNG Magic End-of-File Marker (IEND)
    private static boolean isPngValid(File file) {
        if (!file.exists() || file.length() < 12) return false;

        try (java.io.RandomAccessFile raf = new java.io.RandomAccessFile(file, "r")) {
            raf.seek(file.length() - 12); // Seek to end
            byte[] footer = new byte[12];
            raf.readFully(footer);

            // Hex signature for IEND chunk: 00 00 00 00 49 45 4E 44 AE 42 60 82
            // We check the last 4 bytes: AE 42 60 82
            return (footer[8] == (byte) 0xAE &&
                    footer[9] == (byte) 0x42 &&
                    footer[10] == (byte) 0x60 &&
                    footer[11] == (byte) 0x82);
        } catch (Exception e) {
            return false;
        }
    }
}