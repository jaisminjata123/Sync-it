/* eslint-disable import/no-anonymous-default-export */
import React from "react";
import { useLocation } from "react-router-dom";
import queryString from "query-string";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";
const tokenURL = `${API_URL}/api/spotify/get-token`;

const fetchTokenFromBackend = async (authToken) => {
  try {
    const response = await axios.get(tokenURL, {
      params: { code: authToken },
    });
    return response;
  } catch (err) {
    throw err;
  }
};

export default () => {
  const location = useLocation();
  console.log(location);
  const hello = queryString.parse(location.search);
  console.log(hello);
  const { code } = hello;

  fetchTokenFromBackend(code)
    .then(({ data }) => {
      const { auth_token } = data;
      const { access_token } = auth_token;
      console.log("Received auth token from get-token", access_token);
      localStorage.setItem("spotify-access-token", access_token);
    })
    .catch((err) => {
      console.error(err);
    });

  localStorage.setItem("spotify-auth-token", code);

  return (
    <>
      <h1>Spotify account verified!</h1>
      <div>{code}</div>
    </>
  );
};
