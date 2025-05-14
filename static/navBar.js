const titles = {
  "파티 만들기": "navbarMakeParty",
  "신청한 파티": "navbarUsersRooms",
  "파티 찾기": "navbarRooms",
  "파티 수정하기": "navbarUsersRooms",
  "파티 세부사항": "navbarUsersRooms",
};

for (let t in titles) {
  if (document.title.includes(t)) {
    console.log(t, titles[t]);
    document.getElementById(titles[t])?.classList.add("active");
    break;
  }
}
