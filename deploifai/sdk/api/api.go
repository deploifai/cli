//go:generate go run github.com/Khan/genqlient
package api

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"

	"github.com/Khan/genqlient/graphql"
)

type APIClient struct {
	ClientObject  graphql.Client
	ClientCreated bool
}

func CreateClient() APIClient {
	var backendURL string = os.Getenv("backend_url")
	httpClient := http.Client{}
	apiClient := APIClient{}
	apiClient.ClientObject = graphql.NewClient(fmt.Sprintf("%s/graphql", backendURL), &httpClient)
	apiClient.ClientCreated = true
	return apiClient
}

func (apiClient *APIClient) GetUser() (*GetUserResponse, error) {
	if apiClient.ClientCreated {
		user, err := GetUser(context.Background(), apiClient.ClientObject)
		if err != nil {
			return nil, err
		}
		return user, nil
	}
	return nil, errors.New("Client is not created")
}
