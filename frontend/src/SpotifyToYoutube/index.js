/* eslint-disable import/no-anonymous-default-export */
import React, { useState } from "react";
import "./index.css";
import Header from "../Header";
import FormComponent from "../FormComponent";
import axios from "axios";
import { Spinner, ListGroup } from "react-bootstrap";
import {
  currentDev,
  cycleDev,
  convertSpotifyIdToLink,
  convertYoutubeIdToLink,
} from "../swapYtDev";
import LS from "../assets/ls.png";
import LY from "../assets/ly.png";
import Youtube from "../assets/youtube.png";
import Spotify from "../assets/spotify.png";

const API_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";
const loginURL = `${API_URL}/api/spotify-login`;
const convertURL = `${API_URL}/api/sp-yt/playlist`;
const youtubeLoginURL = `${API_URL}/api/youtube-login`;

const fetchSpotifyAuthToken = async () => {
  try {
    return await axios.get(loginURL);
  } catch (err) {
    console.log(err);
    throw err;
  }
};

const getSpotifyAuthToken = async () => {
  let loginResponse = await fetchSpotifyAuthToken();
  const { data } = loginResponse;
  const { auth_url } = data;
  if (auth_url) {
    console.log(`Opening ${auth_url} in new tab!`);
    window.open(auth_url, "_blank");
    return null;
    // this flow finishes here
  }
  // it reaches here if auth_url is not present in data
  // which means it is logged in!
  const { auth_token } = data;
  console.log(auth_token);
  const { access_token } = auth_token;
  console.log(access_token);
  return access_token;
};

const handleLogin = (responseStatus, depth = 0) => {
  if (depth > 5) {
    window.alert("Over!");
    return;
  }
  let url = `${youtubeLoginURL}`;
  let uniqueId = localStorage.getItem("yt-token");
  let ytDev = currentDev();

  url = `${url}/?id=${ytDev}&username=${uniqueId}/`;

  console.log(responseStatus, "YE HAI");

  if (responseStatus === 501 || responseStatus === 302) {
    return window.open(`${url}`, "_blank");
  } else if (responseStatus === 502) {
    cycleDev();
    ytDev = currentDev();
    return window.open(`${url}`, "_blank");
    // window.alert("Please try again!");
    // return;
  }

  return new Promise(async (resolve, reject) => {
    try {
      console.log("ISS URL PE MAARUNGA", url);
      const response = await axios.get(url);
      console.log(`Youtube login success`, response);
      resolve(response);
    } catch (err) {
      console.error(`Youtube-login`, err.status);
      if (!err.status) {
        handleLogin(501, depth + 1);
      } else {
        const { status } = err.response;
        console.log("YE STATUS AAYA HAI", status);
      }
      return reject(err);
    }
  });
};

const convertPlaylist = async (
  playlistId,
  playlist_target,
  token,
  status = "public",
  username,
  isUrl
) => {
  try {
    let payload = {
      playlistId,
      auth_token: token,
      status,
      username,
    };

    if (isUrl) {
      payload["target_playlist_id"] = playlist_target;
    } else {
      payload["playlist_name"] = playlist_target;
    }

    const response = await axios.post(convertURL, payload);
    return response.data.data;
  } catch (err) {
    throw err;
  }
};

export default () => {
  const [hitConvert, setHitConvert] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [plData, setPlData] = useState({});

  const onConvert = async (id, name, status, isUrl) => {
    try {
      console.log("Calling handleLogin");
      const res_yt = await handleLogin();
      console.log("res_yt", res_yt);
      console.log(res_yt);
      setHitConvert(true);
      let spotifyAccessToken = localStorage.getItem("spotify-access-token");
      console.log(`Fetched from localstorage`, spotifyAccessToken);
      if (!spotifyAccessToken) {
        spotifyAccessToken = await getSpotifyAuthToken();
      }
      if (spotifyAccessToken === null) {
        return window.alert("Account verified! Please press Convert again!");
      }
      setIsLoaded(false);
      let uniqueId = localStorage.getItem("yt-token");
      const response = await convertPlaylist(
        id,
        name,
        spotifyAccessToken,
        status,
        uniqueId,
        isUrl
      );
      console.log(response);
      setIsLoaded(true);
      setPlData(response);
    } catch (err) {
      setIsLoaded(true);
      console.error(err);
    }
  };

  const renderResults = () => {
    const { link = "", mapped_list = [], unmapped_list = [] } = plData;
    const lenMappedSongs = mapped_list.length;
    const lenUnmappedSongs = unmapped_list.length;
    const totalSongs = lenMappedSongs + lenUnmappedSongs;
    const spLink = `https://www.youtube.com/playlist?list=${link}`;

    return (
      <div className="container-div">
        <div className="bubble">
          {!isLoaded && (
            <div className="loader">
              <Spinner
                animation="grow"
                role="status"
                style={{ marginRight: "1rem" }}
              ></Spinner>
              <span>Loading</span>
            </div>
          )}
          {isLoaded && (
            <div className="d-flex flex-column">
              <h4>{`Total: ${totalSongs} Success: ${lenMappedSongs} Error: ${lenUnmappedSongs}`}</h4>
              <h4>
                Link:&nbsp;
                <a href={spLink} rel="noreferrer" target="_blank">
                  <img alt="Spotify" src={LY} height={30}></img>
                </a>
              </h4>
              <div>
                <h4 style={{ marginBottom: "2rem" }}>Mapped Songs</h4>
                <ListGroup>
                  {mapped_list.map((song) => (
                    <ListGroup.Item>
                      <a
                        target="_blank"
                        rel="noreferrer"
                        href={convertSpotifyIdToLink(song["sp_uri"])}
                      >
                        <img alt="Spotify" src={Spotify} height={20}></img>
                      </a>
                      <a
                        style={{ marginLeft: "1rem" }}
                        href={convertYoutubeIdToLink(song["yt_video_id"])}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <img alt="YouTube" src={Youtube} height={20}></img>
                      </a>
                      <span style={{ marginLeft: "1rem" }}>
                        {song["title"] || "Unknown Title"}
                      </span>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </div>
              <div style={{ marginTop: "2rem" }}>
                <h4 style={{ marginBottom: "2rem" }}>Unmapped Songs</h4>
                <ListGroup>
                  {unmapped_list.map((song) => (
                    <ListGroup.Item>
                      <a
                        href={convertSpotifyIdToLink(song["videoId"])}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <img alt="Spotify" src={Spotify} height={20}></img>
                      </a>
                      <span style={{ marginLeft: "1rem" }}>
                        {song["title"] || "Unknown Title"}
                      </span>
                      <span style={{ marginLeft: "1rem" }}>
                        Owner: {song["videoOwner"]}
                      </span>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      <Header />
      <div className="sp-to-yt">
        <FormComponent
          mode="sp2yt"
          getAuthToken={getSpotifyAuthToken}
          onConvert={onConvert}
        />
      </div>
      {hitConvert && renderResults()}
    </>
  );
};
