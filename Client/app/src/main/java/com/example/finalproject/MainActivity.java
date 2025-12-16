package com.example.finalproject;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";

    // ADB Reverse URL (Stable)
//    private static final String SERVER_URL = "http://127.0.0.1:8000/api_root/Post/";
    private static final String SERVER_URL = "https://laurelwoods0102.pythonanywhere.com/api_root/Post/";

    private String authToken;
    private TextView statusTextView;
    private RecyclerView recyclerView;
    private Button btnSync, btnAnalysis, btnLogout;

    private final Executor executor = Executors.newSingleThreadExecutor();
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Enforce Login
        authToken = getIntent().getStringExtra("TOKEN");
        if (authToken == null || authToken.isEmpty()) {
            redirectToLogin();
            return;
        }

        statusTextView = findViewById(R.id.statusTextView);
        recyclerView = findViewById(R.id.recyclerView);

        // [FIX] Bind all 3 buttons
        btnSync = findViewById(R.id.btn_sync);
        btnAnalysis = findViewById(R.id.btn_analysis);
        btnLogout = findViewById(R.id.btn_logout);

        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        // Listeners
        btnSync.setOnClickListener(v -> fetchPosts(SERVER_URL));

        // [NEW] Open Analysis Page
        btnAnalysis.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, AnalysisActivity.class);
            intent.putExtra("TOKEN", authToken);
            startActivity(intent);
        });

        btnLogout.setOnClickListener(v -> redirectToLogin());

        // Initial Load
        fetchPosts(SERVER_URL);
    }

    private void redirectToLogin() {
        Intent intent = new Intent(MainActivity.this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private void fetchPosts(final String urlString) {
        statusTextView.setText("Syncing...");
        executor.execute(() -> {
            String status = "Connection failed.";
            List<Post> posts = null;
            HttpURLConnection conn = null;

            try {
                URL url = new URL(urlString);
                conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("Authorization", "Token " + authToken);
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) response.append(line);
                    reader.close();

                    posts = parsePosts(response.toString());
                    status = "Intrusion Alert Log";
                } else {
                    status = "Server Error: " + conn.getResponseCode();
                    if (conn.getResponseCode() == 401) {
                        handler.post(this::redirectToLogin);
                        return;
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Fetch Error", e);
                status = "Error: " + e.getMessage();
            } finally {
                if (conn != null) conn.disconnect();
            }

            final List<Post> finalPosts = posts;
            final String finalStatus = status;

            handler.post(() -> {
                statusTextView.setText(finalStatus);
                if (finalPosts != null) {
                    ImageAdapter adapter = new ImageAdapter(finalPosts);
                    recyclerView.setAdapter(adapter);
                } else {
                    Toast.makeText(MainActivity.this, finalStatus, Toast.LENGTH_SHORT).show();
                }
            });
        });
    }

    private List<Post> parsePosts(String jsonResponse) {
        List<Post> posts = new ArrayList<>();
        try {
            JSONArray jsonArray = new JSONArray(jsonResponse);
            for (int i = 0; i < jsonArray.length(); i++) {
                JSONObject obj = jsonArray.getJSONObject(i);
                posts.add(new Post(
                        obj.optString("title", "Alert"),
                        obj.optString("text", ""),
                        obj.optString("created_date", ""),
                        obj.optString("image", ""),
                        obj.optString("confidence", "N/A"),
                        obj.optString("bbox", "N/A")
                ));
            }
        } catch (Exception e) {
            Log.e(TAG, "JSON Error", e);
        }
        return posts;
    }
}