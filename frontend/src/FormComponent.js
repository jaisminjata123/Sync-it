/* eslint-disable import/no-anonymous-default-export */
import React, { useState } from "react";
import { Form, Button, Alert } from "react-bootstrap";
import DownArrow from "./assets/downloading_white_48dp.svg";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";
const youtubePlaylistFetchURL = `${API_URL}/api/youtube-playlist-metadata`;
const spotifyYoutubePlaylistFetchURL = `${API_URL}/api/spotify-playlist-metadata`;

const extractSpotifyId = (url) => {
  let id = url;
  let regexPattern = new RegExp(".*/playlist/(.*)(?:\\?.*)?", "i");
  let match = id.match(regexPattern)[1];
  match = match.split("?")[0];
  return match;
};

const extractYoutubeId = (url) => {
  let id = url;
  let match = id.split("list=")[1];
  return match;
};

const fetchYoutubePlaylistDetails = async (id) => {
  let username = localStorage.getItem("yt-token");

  try {
    const { data } = await axios.post(youtubePlaylistFetchURL, {
      playlistId: id,
      username,
    });
    console.log(data);
    const { metadata } = data;

    return {
      owner: metadata["channel_title"],
      description: metadata["description"],
      status: metadata["status"],
      title: metadata["title"],
    };
  } catch (err) {
    if (err.response) {
      console.log(err.response);
      throw err.response.status;
    }
    throw err;
  }
};

const fetchSpotifyPlaylistDetails = async (id, authToken) => {
  console.log(authToken + " AUTH TOKEN");
  try {
    const { data } = await axios.post(spotifyYoutubePlaylistFetchURL, {
      playlistId: id,
      auth_token: authToken,
    });
    const { metadata } = data;
    return {
      owner: metadata["owner"]["display_name"],
      description: metadata["description"],
      status: metadata["public"] ? "public" : "private",
      title: metadata["name"],
    };
  } catch (err) {
    throw err;
  }
};

export default (props) => {
  const {
    mode = "sp2yt",
    onConvert = () => {},
    plData = {},
    handleGoogleLogin,
    getAuthToken = () => {},
  } = props;

  // const [url, setUrl] = useState(
  //   mode === "sp2yt"
  //     ? "https://open.spotify.com/playlist/4bnqXN2jgcHHVI1Vr6Jfhs"
  //     : "https://www.youtube.com/playlist?list=PLf8HsGQSTWJuhLrovf13prQArGRgeGDNT"
  // );

  const [url, setUrl] = useState("");

  const [name, setName] = useState("New Playlist");
  const [isVerified, setVerified] = useState(false);
  const [playlistData, setPlaylistData] = useState({});
  const [targetUrl, setTargetUrl] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    let match = isSp2yt() ? extractSpotifyId(url) : extractYoutubeId(url);
    console.log(`Extracted ID`, match);
    let username = localStorage.getItem("yt-token");

    console.log(targetUrl);

    let target = name;

    let isUrl = false;
    if (targetUrl.length) {
      isUrl = true;
      target = !isSp2yt()
        ? extractSpotifyId(targetUrl)
        : extractYoutubeId(targetUrl);
    }

    console.log(plData);

    onConvert(
      match, //id
      target, //name
      playlistData["status"],
      isUrl
    );
  };

  const onVerifyYoutube = async (e) => {
    e.preventDefault();
    setVerified(false);
    setPlaylistData({});
    try {
      const data = await fetchYoutubePlaylistDetails(extractYoutubeId(url));
      setPlaylistData(data);
      console.log(data);
      setVerified(true);
    } catch (err) {
      console.error(err);
      try {
        const loginRes = await handleGoogleLogin(err);
        console.log(`Successfully logged in Google!`, loginRes);
      } catch (er) {
        console.error(`Google login mein error`, er);
      }
    }
  };

  const onVerifySpotify = async (e) => {
    console.log(url);
    e.preventDefault();
    setVerified(false);
    setPlaylistData({});
    try {
      let spotifyAccessToken = localStorage.getItem("spotify-access-token");
      console.log(`Fetched from localstorage`, spotifyAccessToken);
      if (!spotifyAccessToken) {
        spotifyAccessToken = await getAuthToken();
      }
      if (spotifyAccessToken === null) {
        return window.alert("Account verified! Please press Convert again!");
      }
      const data = await fetchSpotifyPlaylistDetails(
        extractSpotifyId(url),
        spotifyAccessToken
      );
      setPlaylistData(data);
      setVerified(true);
    } catch (err) {
      // console.log("YAHAN KYA HANDLE KARNA HAI? " + err);
      setVerified(true);
      if (err.response) {
        window.alert(JSON.stringify(err.response));
      } else {
        // window.alert("Check console!");
      }
      console.error(err);
    }
  };

  const isSp2yt = () => {
    return mode === "sp2yt";
  };

  return (
    <div
      className="d-flex flex-column align-items-center"
      style={{
        padding: "3rem 4rem",
        backgroundColor: isSp2yt() ? "#1DB954" : "#f44336",
        borderRadius: ".5rem",
      }}
    >
      <Form
        style={{
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
        onSubmit={onSubmit}
      >
        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Form.Group controlId="formBasicEmail" style={{ width: "75%" }}>
            <Form.Label style={{ fontSize: "1.5rem", fontWeight: "600" }}>
              {isSp2yt() ? "Spotify" : "Youtube"} Playlist Link
            </Form.Label>
            <Form.Control
              required
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Eg: https://open.spotify.com/playlist/1Wr1URyL0fZcW10cHyxgpj"
            />
            <Button
              className="mt-2"
              size="sm"
              variant="primary"
              onClick={isSp2yt() ? onVerifySpotify : onVerifyYoutube}
            >
              Verify
            </Button>
            {isVerified && (
              <div className="mt-3">
                <Alert variant="success">
                  {`Title: ${playlistData["title"]} Owner: ${playlistData["owner"]} Status: ${playlistData["status"]}`}
                </Alert>
              </div>
            )}
          </Form.Group>
          <Form.Group>
            <div
              style={{
                margin: "3rem 4rem 2rem 4rem",
                transform: "rotate(-90deg)",
              }}
            >
              <img src={DownArrow} height="75" alt="Down Arrow" />
            </div>
          </Form.Group>
          <Form.Group controlId="formBasicEmail" style={{ width: "75%" }}>
            <Form.Label style={{ fontSize: "1.5rem", fontWeight: "600" }}>
              {isSp2yt() ? "Youtube" : "Spotify"} Playlist Name
            </Form.Label>
            <Form.Control
              type="text"
              placeholder="Eg: New Playlist"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <div className="my-2" style={{ marginTop: "4rem" }}>
              <b>OR</b>
            </div>
            <Form.Label style={{ fontSize: "1.5rem", fontWeight: "600" }}>
              {isSp2yt() ? "Youtube" : "Spotify"} URL
            </Form.Label>
            <Form.Control
              type="text"
              placeholder={`Eg: ${
                isSp2yt()
                  ? "https://open.spotify.com/playlist/4bnqXN2jgcHHVI1Vr6Jfhs"
                  : "https://www.youtube.com/playlist?list=PLf8HsGQSTWJuhLrovf13prQArGRgeGDNT"
              }`}
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
            />
          </Form.Group>
        </div>
        <div>
          <Button
            className="mt-1"
            variant="light"
            type="submit"
            disabled={!isVerified}
          >
            Convert
          </Button>
        </div>
      </Form>
    </div>
  );
};
