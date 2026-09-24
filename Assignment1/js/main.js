// Assignment1 - 名著解说视频《你当像鸟飞往你的山》
// 交互：导航高亮 + 滚动浮现动画

document.addEventListener("DOMContentLoaded", function () {
  // 滚动浮现
  var reveals = document.querySelectorAll(".reveal");
  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  reveals.forEach(function (el) { io.observe(el); });

  // 导航高亮
  var links = document.querySelectorAll("nav a");
  var sections = [];
  links.forEach(function (a) {
    var id = a.getAttribute("href").slice(1);
    var sec = document.getElementById(id);
    if (sec) sections.push({ link: a, sec: sec });
  });
  window.addEventListener("scroll", function () {
    var cur = sections[0];
    sections.forEach(function (item) {
      if (item.sec.getBoundingClientRect().top < 140) cur = item;
    });
    links.forEach(function (a) { a.classList.remove("active"); });
    if (cur) cur.link.classList.add("active");
  }, { passive: true });
});
