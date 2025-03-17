const express = require("express");
const fs = require("fs");
const { exec } = require("child_process");

const app = express();
app.use(express.static(__dirname)); // يسمح بتحميل HTML مباشرة
app.use(express.json());

let processInstance = null; // لتخزين عملية تشغيل البايثون

// حفظ الكود في ملف
app.post("/save", (req, res) => {
    const { filename, code } = req.body;
    fs.writeFile(filename, code, (err) => {
        if (err) return res.status(500).send("حدث خطأ أثناء الحفظ");
        res.send(`تم حفظ الكود في ${filename}`);
    });
});

// تشغيل الكود
app.get("/start", (req, res) => {
    if (processInstance) return res.send("الكود يعمل بالفعل!");

    processInstance = exec("python script.py", (error, stdout, stderr) => {
        processInstance = null;
        res.send(stdout + (stderr ? "\n" + stderr : ""));
    });
});

// إيقاف التنفيذ
app.get("/stop", (req, res) => {
    if (processInstance) {
        processInstance.kill();
        processInstance = null;
        res.send("تم إيقاف الكود.");
    } else {
        res.send("لا يوجد كود يعمل حالياً.");
    }
});

// تشغيل السيرفر
app.listen(3000, () => console.log("السيرفر يعمل على http://localhost:3000"));
