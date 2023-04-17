export const currentDev = () => {
  return localStorage.getItem("yt-dev");
};

export const cycleDev = () => {
  let code = localStorage.getItem("yt-dev");
  code = parseInt(code);
  code = code + 1;
  if (code > 2) code = 0;
  localStorage.setItem("yt-dev", code);
};

export const convertSpotifyIdToLink = (id) => {
  id = id.split(":")[2]
  return `https://open.spotify.com/track/${id}`;
};

export const convertYoutubeIdToLink = (id) => {
  return `https://youtu.be/${id}`;
};
