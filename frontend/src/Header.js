/* eslint-disable import/no-anonymous-default-export */
import React from "react";
import { useHistory } from "react-router-dom";
import { Button } from "react-bootstrap";

export default (props) => {
  const history = useHistory();

  return (
    <div className="header">
      <div className="bubble text-white d-flex flex-column align-items-center">
        <h1>SyncIt</h1>
        <div className="mt-2">
          <Button
            variant="success"
            className="mx-2"
            onClick={() => history.push("/sp2yt")}
          >
            Spotify to Youtube
          </Button>
          <Button variant="danger" onClick={() => history.push("/yt2sp")}>
            Youtube to Spotify
          </Button>
        </div>
      </div>
    </div>
  );
};
