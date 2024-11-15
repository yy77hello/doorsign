#include "esp_camera.h"
#include <WiFi.h>
#include <ESP_Mail_Client.h>

// Wi-Fi credentials
const char* ssid = "Enter here";
const char* password = "Enter here";

// Email configuration
#define emailSenderAccount    "Enter here"
#define emailSenderPassword   "Enter here"
#define emailRecipient        "Enter here"
#define smtpServer            "smtp.gmail.com"
#define smtpServerPort        587

// Flash configuration
const byte flashPin = 4;  // GPIO4 for ESP32-CAM flash
const byte ledPin = 2;     // GPIO2 for flickering LED (change as needed)
const uint32_t freq = 5000;
const uint8_t ledChannel = 0;
const uint8_t pwmResolution = 8;

void takePictureAndSendEmail();

// Camera pins for ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
    Serial.begin(115200);
    // while (!Serial) { delay(100); }
    Serial.println("ESP32-CAM initializing...");

    // Initialize LED pin
    pinMode(flashPin, OUTPUT);
    
    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
        delay(500);
        Serial.print(".");
    }
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Failed to connect to WiFi. Restarting...");
        ESP.restart();
    }
    Serial.println("\nConnected to WiFi");

    // Initialize camera
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return;
    }
    Serial.println("Camera initialized successfully");
        flashOn(); // Flicker LED 
        takePictureAndSendEmail();
        delay(300); // Keep it on for a brief moment
        flashOff(); // Turn off the LED after flickering

}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        Serial.println("Received command: " + command);
        if (command == "take_picture") {
            flashOn(); // Flicker LED on receiving command
            delay(300); // Keep it on for a brief moment
            flashOff(); // Turn off the LED after flickering                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
            Serial.println("Taking picture command received."); // Debug statement

            takePictureAndSendEmail();
        }
    }
    delay(100); // Small delay to prevent tight looping
}

void flashOn() {
    digitalWrite(flashPin, HIGH);
    Serial.println("Flash ON");
}

void flashOff() {
    digitalWrite(flashPin, LOW); // Turn off the flickering LED
    Serial.println("Flash OFF");
}

void takePictureAndSendEmail() {
    
   camera_fb_t * fb = esp_camera_fb_get();

   if (!fb) {
       Serial.println("Camera capture failed");
       return;
   }

   if (WiFi.status() != WL_CONNECTED) {
       Serial.println("WiFi disconnected. Reconnecting...");
       WiFi.reconnect();
       delay(5000); // Wait for reconnection
   }

   ESP_Mail_Session session;
   session.server.host_name = smtpServer;
   session.server.port = smtpServerPort;
   session.login.email = emailSenderAccount;
   session.login.password = emailSenderPassword;

   SMTP_Message message;
   message.sender.name = "ESP32-CAM";
   message.sender.email = emailSenderAccount;
   message.subject = "Doorsign Visitor";
   message.addRecipient("Office Owner", emailRecipient);
   message.text.content = "Someone tapped on the doorsign. Picture attached.";

   SMTP_Attachment att;
   att.descr.filename = "picture.jpg";
   att.descr.mime = "image/jpg";
   att.blob.data = fb->buf;
   att.blob.size = fb->len;

   message.addAttachment(att);

   SMTPSession smtp;

   bool emailSent = false;
   int retries = 3;

   while (!emailSent && retries > 0) {
       if (smtp.connect(&session)) {
           Serial.println("Session exists");
           if (MailClient.sendMail(&smtp, &message)) {
               Serial.println("Email sent successfully");
               emailSent = true;
           } else {
               Serial.println("Error sending Email, " + smtp.errorReason());
           }
       } else {
           Serial.println("SMTP server connection failed");
       }
       retries--;
       if (!emailSent && retries > 0) delay(5000); // Wait before retrying
   }

   esp_camera_fb_return(fb);
}