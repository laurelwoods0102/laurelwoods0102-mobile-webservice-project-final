package com.example.finalproject;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.squareup.picasso.Picasso;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

public class AnalysisActivity extends AppCompatActivity {
//    private static final String ANALYSIS_URL = "http://10.0.2.2:8000/api_root/analysis/"; // or 127.0.0.1 with ADB reverse
    private static final String ANALYSIS_URL = "https://laurelwoods0102.pythonanywhere.com/api_root/analysis/";

    private TextView tvSummary, tvPeopleHeader;
    private LinearLayout layoutPlots, layoutPeopleGroups;
    private String authToken;

    private final Executor executor = Executors.newSingleThreadExecutor();
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_analysis);

        tvSummary = findViewById(R.id.tv_summary);
        tvPeopleHeader = findViewById(R.id.tv_people_header);
        layoutPlots = findViewById(R.id.layout_plots);
        layoutPeopleGroups = findViewById(R.id.layout_people_groups);

        authToken = getIntent().getStringExtra("TOKEN");
        fetchAnalysis();
    }

    private void fetchAnalysis() {
        executor.execute(() -> {
            try {
                URL url = new URL(ANALYSIS_URL);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("Authorization", "Token " + authToken);

                int code = conn.getResponseCode();
                if (code == 200) {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) response.append(line);

                    JSONObject json = new JSONObject(response.toString());
                    handler.post(() -> updateUI(json));
                } else {
                    handler.post(() -> Toast.makeText(this, "Failed: " + code, Toast.LENGTH_SHORT).show());
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    private void updateUI(JSONObject json) {
        try {
            // 1. Summary
            tvSummary.setText(json.optString("summary", "No data"));

            // 2. General Plots (Pie/Bar)
            layoutPlots.removeAllViews();
            JSONArray plots = json.optJSONArray("plot_urls");
            if (plots != null) {
                for (int i = 0; i < plots.length(); i++) {
                    addImageToLayout(layoutPlots, plots.getString(i), 600);
                }
            }

            // 3. People Groups (Structured)
            layoutPeopleGroups.removeAllViews();
            JSONArray people = json.optJSONArray("people_data");

            if (people != null && people.length() > 0) {
                tvPeopleHeader.setVisibility(android.view.View.VISIBLE);

                for (int i = 0; i < people.length(); i++) {
                    JSONObject p = people.getJSONObject(i);
                    int id = p.optInt("id");
                    int count = p.optInt("count");
                    String url = p.optString("url");

                    // Create a "Card" container
                    LinearLayout card = new LinearLayout(this);
                    card.setOrientation(LinearLayout.VERTICAL);
                    card.setBackgroundColor(Color.WHITE);
                    card.setPadding(20, 20, 20, 20);
                    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                    params.setMargins(0, 0, 0, 40);
                    card.setLayoutParams(params);
                    card.setElevation(6f);

                    // Label: "Person #1 (seen 5 times)"
                    TextView label = new TextView(this);
                    label.setText("Person #" + id + " (Seen " + count + " times)");
                    label.setTextSize(16);
                    label.setTypeface(null, Typeface.BOLD);
                    label.setTextColor(Color.BLACK);
                    label.setPadding(0,0,0,15);
                    card.addView(label);

                    // Collage Image
                    ImageView iv = new ImageView(this);
                    LinearLayout.LayoutParams imgParams = new LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT, 500); // Fixed height for consistency
                    iv.setLayoutParams(imgParams);
                    iv.setScaleType(ImageView.ScaleType.FIT_CENTER);
                    Picasso.get().load(url).placeholder(android.R.drawable.ic_menu_gallery).into(iv);

                    card.addView(iv);
                    layoutPeopleGroups.addView(card);
                }
            } else {
                tvPeopleHeader.setVisibility(android.view.View.GONE);
                TextView noData = new TextView(this);
                noData.setText("No people identified.");
                noData.setGravity(Gravity.CENTER);
                layoutPeopleGroups.addView(noData);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void addImageToLayout(LinearLayout layout, String url, int height) {
        ImageView iv = new ImageView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, height);
        params.setMargins(0, 0, 0, 30);
        iv.setLayoutParams(params);
        iv.setScaleType(ImageView.ScaleType.FIT_CENTER);
        iv.setBackgroundColor(Color.WHITE);
        iv.setElevation(4f);
        layout.addView(iv);
        Picasso.get().load(url).into(iv);
    }
}